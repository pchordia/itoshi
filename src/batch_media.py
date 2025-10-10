#!/usr/bin/env python3
"""
Batch media processor:
- anime:   Convert images in a directory to anime-styled images via OpenAI gpt-image-1 using prompts from a text file
- i2v:     Convert images in a directory to videos via Kling Professional v2.1 using prompts from a text file
- analyze: Send images to an OpenAI chat model with a template prompt and save structured descriptions

Features:
- Up to 30 parallel workers
- Exponential backoff with jitter for transient errors
- Random prompt selection when multiple prompts are provided (anime/i2v)
- .env support for API keys and defaults

Note on Kling API: This script targets Kling image-to-video (Professional v2.1) 5s by default.
Adjust via CLI flags.
"""

import os
import sys
import time
import json
import base64
import random
import argparse
import threading
import re
from typing import List, Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from tqdm import tqdm
import jwt
import csv
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

# Load env early
load_dotenv()

# Env / defaults
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY", "")
KLING_ACCESS_KEY_ID = os.getenv("KLING_ACCESS_KEY_ID", "")
KLING_SECRET_ACCESS_KEY = os.getenv("KLING_SECRET_ACCESS_KEY", "")
KLING_BASE_URL = os.getenv("KLING_BASE_URL", "https://app.klingai.com")
KLING_CREATE_URL = os.getenv(
    "KLING_CREATE_URL",
    "https://api-singapore.klingai.com/v1/videos/image2video",
)
KLING_STATUS_URL_TEMPLATE = os.getenv(
    "KLING_STATUS_URL_TEMPLATE",
    "https://api-singapore.klingai.com/v1/videos/image2video/{task_id}",
)
ANIME_MAX_WORKERS = int(os.getenv("ANIME_MAX_WORKERS", "20"))
I2V_MAX_WORKERS = int(os.getenv("I2V_MAX_WORKERS", "10"))
KLING_MAX_WORKERS = int(os.getenv("KLING_MAX_WORKERS", "20"))  # Kling has stricter rate limits
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "30"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "6"))
INITIAL_BACKOFF_SECONDS = float(os.getenv("INITIAL_BACKOFF_SECONDS", "1"))
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "auto")
VIDEO_DURATION_SECONDS = int(os.getenv("VIDEO_DURATION_SECONDS", "5"))
KLING_MODEL = os.getenv("KLING_MODEL", "Professional v2.1")
ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", "gpt-5")
I2V_MODEL = os.getenv("I2V_MODEL", "kling")
VEO_MODEL = os.getenv("VEO_MODEL", "veo-3.0-generate-001")
GOOGLE_IMAGE_MODEL = os.getenv("GOOGLE_IMAGE_MODEL", "imagen-3.0-generate-001")
GOOGLE_GEMINI_IMAGE_MODEL = os.getenv("GOOGLE_GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview")

# ============= i2i to i2v Style Mappings =============
# Automatically link certain i2i (anime) styles with specific i2v styles
# When an i2i style in this dict is used, the corresponding i2v style will be used automatically
I2I_TO_I2V_STYLE_MAP = {
	"cartoonSaloon": "cartoonSaloon",
	"demonslayer": "demonslayer",
	"demonslayer2": "demonslayer",  # Both demonslayer i2i styles map to the same i2v
	"demonhunter": "demonhunter",
	"claymation": "claymation",
	"lego": "lego",
	"peanuts": "peanuts",
	"antiquepuppet": "antiquepuppet",
	"antiquepuppetcreepy": "antiquepuppet",  # antiquepuppetcreepy i2i maps to antiquepuppet i2v
	"corpsebride": "corpsebride",
	"french": "french",
	"japaneseNoodleShop": "japaneseNoodleShop",
}


def get_linked_i2v_style(i2i_style_name: str) -> Optional[str]:
	"""
	Get the recommended i2v style for a given i2i style.
	Returns the i2v style name if a mapping exists, None otherwise.
	"""
	return I2I_TO_I2V_STYLE_MAP.get(i2i_style_name)


# Validate keys presence at runtime per subcommand


def read_prompts_file(path: str) -> List[str]:
	with open(path, "r", encoding="utf-8") as f:
		prompts = [line.strip() for line in f.readlines() if line.strip()]
	if not prompts:
		raise ValueError(f"No prompts found in {path}")
	return prompts

def read_named_prompts(path: str) -> List[Tuple[str, str]]:
	"""Parses a prompts file supporting either:
	- plain lines (no name): returns [("", line), ...]
	- named lines: "name: prompt text" -> [(name, prompt), ...]
	Ignores comment lines starting with '#'.
	"""
	entries: List[Tuple[str, str]] = []
	with open(path, "r", encoding="utf-8") as f:
		for raw in f.readlines():
			line = raw.strip()
			if not line or line.startswith('#'):
				continue
			if ':' in line:
				name, rest = line.split(':', 1)
				entries.append((name.strip(), rest.strip()))
			else:
				entries.append(("", line))
	if not entries:
		raise ValueError(f"No prompts found in {path}")
	return entries


# ============= Gender/Sex Prompt Transformation =============

# Hard pronoun maps (only applied if the prompt already uses gendered pronouns)
PRONOUN_MAPS = {
	"M": [
		(r"\bthey\b", "he"),
		(r"\bthem\b", "him"),
		(r"\btheir\b", "his"),
		(r"\btheirs\b", "his"),
		(r"\bthemself\b", "himself"),
		(r"\bthemselves\b", "himself"),
		(r"\bshe\b", "he"),
		(r"\bher\b", "his"),   # safe when used as possessive
		(r"\bhers\b", "his"),
	],
	"F": [
		(r"\bthey\b", "she"),
		(r"\bthem\b", "her"),
		(r"\btheir\b", "her"),
		(r"\btheirs\b", "hers"),
		(r"\bthemself\b", "herself"),
		(r"\bthemselves\b", "herself"),
		(r"\bhe\b", "she"),
		(r"\bhim\b", "her"),
		(r"\bhis\b", "her"),
	],
}

# Lightweight style cues appended/inserted to tune movement quality
STYLE_TAGS = {
	"M": "Presenting a masculine look and movement quality (confident posture, strong chest/shoulder isolations).",
	"F": "Presenting a feminine look and movement quality (fluid lines, hip emphasis, graceful arm styling).",
}

# Where to inject the style tag: before identity-lock sentence if we can find one
IDENTITY_ANCHORS = [
	"The anime character matches the uploaded reference exactly",
	"The character matches the uploaded reference exactly",
	"Preserve identity",
]

def inject_style_tag(prompt: str, tag: str) -> str:
	"""Try to insert just before the identity anchor; otherwise append at the end."""
	for anchor in IDENTITY_ANCHORS:
		idx = prompt.find(anchor)
		if idx != -1:
			return prompt[:idx].rstrip() + " " + tag + " " + prompt[idx:]
	# fallback: append
	if prompt.strip().endswith("."):
		return prompt.strip() + " " + tag
	return prompt.strip() + ". " + tag

def map_pronouns(prompt: str, gender: str) -> str:
	"""Apply pronoun replacements based on gender."""
	mapped = prompt
	for pat, repl in PRONOUN_MAPS.get(gender, []):
		mapped = re.sub(pat, repl, mapped, flags=re.IGNORECASE)
	return mapped

def tidy_spaces(text: str) -> str:
	"""Remove accidental double spaces from replacements."""
	return re.sub(r"\s{2,}", " ", text).strip()

def genderize_prompt(original: str, gender: str) -> str:
	"""
	Transform a prompt to match a specified gender presentation.
	
	Args:
		original: The original prompt text
		gender: Either "M" (masculine) or "F" (feminine)
	
	Returns:
		Transformed prompt with gender-appropriate styling and pronouns
	"""
	# Keep original choreography/constraints intact
	out = original

	# Inject gentle gender movement cue (non-destructive)
	out = inject_style_tag(out, STYLE_TAGS.get(gender, ""))

	# Harmonize pronouns if any are present
	out = map_pronouns(out, gender)

	# Optional: ensure face/body visibility constraints
	vis_bits = []
	if "entire body" not in out.lower():
		vis_bits.append("Entire body is always in frame.")
	if "head is always in the frame" not in out.lower() and "face" not in out.lower():
		vis_bits.append("Head is always in the frame.")
	if vis_bits:
		out = out.rstrip(". ") + " " + " ".join(vis_bits)

	return tidy_spaces(out)


def ensure_dir(path: str) -> None:
	os.makedirs(path, exist_ok=True)


# ------------------------- metrics logging (anime) -------------------------

CSV_LOCK = threading.Lock()

ANIME_METRIC_HEADERS = [
	"image_name",
	"prompt_name",
	"size_param",
	"input_file_bytes",
	"input_px_w",
	"input_px_h",
	"request_body_bytes",
	"upload_ms",
	"ttfb_ms",
	"resp_download_ms",
	"resp_bytes",
	"result_kind",
	"image_bytes",
	"output_px_w",
	"output_px_h",
	"image_download_ms",
	"total_ms",
	"status",
	"error",
]


def append_anime_metrics_row(out_dir: str, row: dict) -> None:
	"""Append a metrics row into _anime_metrics.csv under out_dir."""
	log_path = os.path.join(out_dir, "_anime_metrics.csv")
	first_write = not os.path.exists(log_path)
	with CSV_LOCK:
		with open(log_path, "a", newline="", encoding="utf-8") as f:
			writer = csv.DictWriter(f, fieldnames=ANIME_METRIC_HEADERS)
			if first_write:
				writer.writeheader()
			writer.writerow({k: row.get(k, "") for k in ANIME_METRIC_HEADERS})


# ------------------------- metrics logging (gemini i2i) -------------------------

GEMINI_I2I_METRIC_HEADERS = [
	"image_name",
	"prompt_name",
	"input_file_bytes",
	"input_px_w",
	"input_px_h",
	"request_time_ms",
	"response_bytes",
	"output_px_w",
	"output_px_h",
	"total_time_ms",
	"status",
	"error",
]


def append_gemini_i2i_metrics_row(out_dir: str, row: dict) -> None:
	"""Append a metrics row into _gemini_i2i_metrics.csv under out_dir."""
	log_path = os.path.join(out_dir, "_gemini_i2i_metrics.csv")
	first_write = not os.path.exists(log_path)
	with CSV_LOCK:
		with open(log_path, "a", newline="", encoding="utf-8") as f:
			writer = csv.DictWriter(f, fieldnames=GEMINI_I2I_METRIC_HEADERS)
			if first_write:
				writer.writeheader()
			writer.writerow({k: row.get(k, "") for k in GEMINI_I2I_METRIC_HEADERS})


# ------------------------- metrics logging (i2v) -------------------------

I2V_METRIC_HEADERS = [
	"image_name",
	"prompt_name",
	"actual_prompt",
	"gender",
	"camera_direction",
	"background",
	"negative_prompt_used",
	"cfg_scale",
	"duration_seconds",
	"input_px_w",
	"input_px_h",
	"input_image_bytes",
	"json_body_bytes",
	"create_upload_ms",
	"create_ttfb_ms",
	"create_resp_download_ms",
	"create_resp_bytes",
	"create_total_ms",
	"task_id",
	"poll_attempts",
	"poll_seconds",
	"video_url",
	"video_ttfb_ms",
	"video_resp_download_ms",
	"video_total_ms",
	"video_bytes",
	"total_end_to_end_ms",
	"status",
	"error",
]


def append_i2v_metrics_row(out_dir: str, row: dict) -> None:
	"""Append a metrics row into _i2v_metrics.csv under out_dir."""
	log_path = os.path.join(out_dir, "_i2v_metrics.csv")
	first_write = not os.path.exists(log_path)
	with CSV_LOCK:
		with open(log_path, "a", newline="", encoding="utf-8") as f:
			writer = csv.DictWriter(f, fieldnames=I2V_METRIC_HEADERS)
			if first_write:
				writer.writeheader()
			writer.writerow({k: row.get(k, "") for k in I2V_METRIC_HEADERS})


def make_unique_output_dir(base_dir: str) -> str:
	"""Create and return a unique subdirectory under base_dir using a timestamp.
	If the timestamp folder exists, appends an incrementing suffix.
	"""
	ensure_dir(base_dir)
	stamp = time.strftime("%y%m%d_%H%M%S")
	candidate = os.path.join(base_dir, stamp)
	idx = 1
	while os.path.exists(candidate):
		candidate = os.path.join(base_dir, f"{stamp}_{idx}")
		idx += 1
	os.makedirs(candidate, exist_ok=True)
	return candidate


def read_text_file(path: str) -> str:
	"""Read an entire text file as a single string (for long template prompts)."""
	with open(path, "r", encoding="utf-8") as f:
		return f.read().strip()


def list_images(path: str) -> List[str]:
	valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
	files = []
	for name in os.listdir(path):
		p = os.path.join(path, name)
		if os.path.isfile(p) and os.path.splitext(name)[1].lower() in valid_exts:
			files.append(p)
	return sorted(files)


# ------------------------- backoff -------------------------

def with_backoff(func: Callable, *, max_retries: int = MAX_RETRIES, initial_delay: float = INITIAL_BACKOFF_SECONDS):
	def wrapper(*args, **kwargs):
		delay = initial_delay
		for attempt in range(max_retries):
			try:
				return func(*args, **kwargs)
			except Exception as e:
				if attempt == max_retries - 1:
					raise
				# jitter 0-0.5s
				jitter = random.random() * 0.5
				time.sleep(delay + jitter)
				delay *= 2
	return wrapper


# ------------------------- OpenAI: gpt-image-1 -------------------------

def openai_generate_anime_image_bytes(src_image_path: str, prompt: str, *, size: str = IMAGE_SIZE, prompt_name: str = "") -> Tuple[bytes, dict]:
	"""Uses OpenAI Images API (gpt-image-1) to stylize into anime.
	Returns (png_bytes, metrics_dict).
	"""
	if not OPENAI_API_KEY:
		raise RuntimeError("OPENAI_API_KEY is required")

	# Detect MIME type from file extension
	ext = os.path.splitext(src_image_path)[1].lower()
	mime_type = {
		'.jpg': 'image/jpeg',
		'.jpeg': 'image/jpeg', 
		'.png': 'image/png',
		'.webp': 'image/webp'
	}.get(ext, 'image/jpeg')

	# Build multipart with monitor to capture upload timing
	input_file_bytes = os.path.getsize(src_image_path)
	# Input pixel dimensions
	try:
		with Image.open(src_image_path) as _im:
			in_w, in_h = _im.size
	except Exception:
		in_w, in_h = ("", "")
	fh = open(src_image_path, "rb")
	fields = {
		"model": "gpt-image-1",
		"prompt": prompt,
		"size": size,
		"quality": "high",
		"n": "1",
		"image": (os.path.basename(src_image_path), fh, mime_type),
	}
	encoder = MultipartEncoder(fields=fields)
	upload_finished_ts = [None]

	def _progress_cb(m: MultipartEncoderMonitor) -> None:
		if m.bytes_read >= encoder.len and upload_finished_ts[0] is None:
			upload_finished_ts[0] = time.perf_counter()

	monitor = MultipartEncoderMonitor(encoder, _progress_cb)
	headers = {
		"Authorization": f"Bearer {OPENAI_API_KEY}",
		"Content-Type": monitor.content_type,
	}

	metrics = {
		"image_name": os.path.basename(src_image_path),
		"prompt_name": prompt_name,
		"size_param": size,
		"input_file_bytes": input_file_bytes,
		"input_px_w": in_w,
		"input_px_h": in_h,
		"request_body_bytes": encoder.len,
		"upload_ms": "",
		"ttfb_ms": "",
		"resp_download_ms": "",
		"resp_bytes": "",
		"result_kind": "",
		"image_bytes": "",
		"output_px_w": "",
		"output_px_h": "",
		"image_download_ms": "",
		"total_ms": "",
		"status": "ok",
		"error": "",
	}

	t0 = time.perf_counter()
	try:
		resp = requests.post(
			"https://api.openai.com/v1/images/edits",
			headers=headers,
			data=monitor,
			stream=True,
			timeout=REQUEST_TIMEOUT_SECONDS,
		)
		# Time to first body byte
		try:
			it = resp.iter_content(chunk_size=65536)
			first_chunk = next(it)
			t2 = time.perf_counter()
			rest_chunks = [c for c in it if c]
			resp_content = first_chunk + b"".join(rest_chunks)
		except StopIteration:
			# No body
			t2 = time.perf_counter()
			resp_content = b""
	finally:
		try:
			fh.close()
		except Exception:
			pass

	if upload_finished_ts[0] is None:
		upload_finished_ts[0] = t2

	t1 = upload_finished_ts[0]
	t3 = time.perf_counter()

	metrics["upload_ms"] = int((t1 - t0) * 1000)
	metrics["ttfb_ms"] = int((t2 - t1) * 1000)
	metrics["resp_download_ms"] = int((t3 - t2) * 1000)
	metrics["resp_bytes"] = len(resp_content)
	metrics["total_ms"] = int((t3 - t0) * 1000)

	if resp.status_code >= 400:
		metrics["status"] = "error"
		metrics["error"] = resp.text[:500]
		raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")

	try:
		data = json.loads(resp_content.decode("utf-8"))
	except Exception as e:
		metrics["status"] = "error"
		metrics["error"] = f"invalid json: {str(e)}"
		raise RuntimeError(f"OpenAI response not valid JSON: {e}. Body: {resp_content[:200]!r}")

	print(f"🔍 Debug: API response keys: {list(data.keys())}")
	if "data" in data and data["data"]:
		print(f"🔍 Debug: First data item keys: {list(data['data'][0].keys())}")

	# Try different response formats
	if data.get("data") and data["data"][0].get("url"):
		image_url = data["data"][0]["url"]
		print(f"🔍 Debug: Found image URL: {image_url[:50]}...")
		# Download the image from URL and measure
		img_t0 = time.perf_counter()
		img_resp = requests.get(image_url, timeout=REQUEST_TIMEOUT_SECONDS)
		img_resp.raise_for_status()
		img_bytes = img_resp.content
		metrics["image_download_ms"] = int((time.perf_counter() - img_t0) * 1000)
		metrics["result_kind"] = "url"
		metrics["image_bytes"] = len(img_bytes)
		try:
			with Image.open(BytesIO(img_bytes)) as _out:
				out_w, out_h = _out.size
				metrics["output_px_w"] = out_w
				metrics["output_px_h"] = out_h
		except Exception:
			pass
		return img_bytes, metrics
	elif data.get("data") and data["data"][0].get("b64_json"):
		image_b64 = data["data"][0]["b64_json"]
		print(f"🔍 Debug: Found base64 data, length: {len(image_b64)}")
		img_bytes = base64.b64decode(image_b64)
		metrics["result_kind"] = "b64"
		metrics["image_bytes"] = len(img_bytes)
		try:
			with Image.open(BytesIO(img_bytes)) as _out:
				out_w, out_h = _out.size
				metrics["output_px_w"] = out_w
				metrics["output_px_h"] = out_h
		except Exception:
			pass
		return img_bytes, metrics
	else:
		metrics["status"] = "error"
		metrics["error"] = f"missing image data: {data}"
		raise RuntimeError(f"OpenAI response missing image data. Full response: {data}")


# ------------------------- OpenAI: Chat image analysis -------------------------

def openai_analyze_image(src_image_path: str, prompt_text: str, *, model: str = ANALYSIS_MODEL) -> str:
	"""Send an image and a template prompt to an OpenAI chat model and return the analysis text (Chat Completions)."""
	if not OPENAI_API_KEY:
		raise RuntimeError("OPENAI_API_KEY is required")

	# Load image and compress to reasonable size for request
	with Image.open(src_image_path) as img:
		if img.mode in ('RGBA', 'LA', 'P'):
			img = img.convert('RGB')
		# Resize to max 1280 on longest side to control payload size
		max_side = 1280
		img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
		buf = BytesIO()
		# Use PNG to match working example's data URL
		img.save(buf, format='PNG', optimize=True)
		img_bytes = buf.getvalue()

	image_b64 = base64.b64encode(img_bytes).decode("utf-8")
	data_url = f"data:image/png;base64,{image_b64}"

	headers = {
		"Authorization": f"Bearer {OPENAI_API_KEY}",
		"Content-Type": "application/json",
	}

	payload = {
		"model": model,
		"messages": [
			{
				"role": "user",
				"content": [
					{"type": "text", "text": prompt_text},
					{"type": "image_url", "image_url": {"url": data_url}},
				],
			}
		],
		"temperature": 0.2,
		"max_tokens": 900,
	}

	resp = requests.post(
		"https://api.openai.com/v1/chat/completions",
		headers=headers,
		data=json.dumps(payload),
		timeout=REQUEST_TIMEOUT_SECONDS,
	)
	if resp.status_code >= 400:
		# Persist full error for debugging
		try:
			ensure_dir("outputs/analysis_errors")
			with open("outputs/analysis_errors/last_error.json", "w", encoding="utf-8") as ef:
				ef.write(resp.text)
		except Exception:
			pass
		raise RuntimeError(f"OpenAI analyze error {resp.status_code}: {resp.text}")
	try:
		data = resp.json()
	except json.JSONDecodeError as e:
		raise RuntimeError(f"Analyze response not valid JSON: {e}. Response: {resp.text[:200]}")

	choices = data.get("choices", [])
	if not choices or not choices[0].get("message", {}).get("content"):
		raise RuntimeError(f"Analyze response missing content: {data}")
	return choices[0]["message"]["content"].strip()


# ------------------------- Kling: image-to-video Professional v2.1 -------------------------

def generate_kling_jwt_token() -> str:
	"""Generate JWT token for Kling AI API authentication based on their docs."""
	if not KLING_ACCESS_KEY or not KLING_SECRET_KEY:
		raise RuntimeError("KLING_ACCESS_KEY and KLING_SECRET_KEY are required")
	
	headers = {
		"alg": "HS256",
		"typ": "JWT",
	}
	
	payload = {
		"iss": KLING_ACCESS_KEY,  # issuer (access key)
		"exp": int(time.time()) + 1800,  # expires in 30 minutes
		"nbf": int(time.time()) - 5,  # not before (current time - 5 seconds)
	}
	
	return jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256", headers=headers)

def kling_create_i2v_task(image_bytes: bytes, prompt: str, *, duration_seconds: int = VIDEO_DURATION_SECONDS, negative_prompt: str = None, cfg_scale: float = 0.5) -> Tuple[str, dict]:
	"""Creates a Kling I2V task and returns (task_id, create_metrics). Uses kling-v2-1 (Professional v2.1) model.
	
	Args:
		cfg_scale: Classifier Free Guidance scale (0.0-1.0). Higher values = stricter adherence to prompt. Default: 0.5
	"""
	# Generate JWT token for authentication
	jwt_token = generate_kling_jwt_token()
	print(f"🔑 Generated JWT token for authentication")

	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {jwt_token}",
	}

	# Convert image to base64 as per TypeScript implementation
	image_base64 = base64.b64encode(image_bytes).decode("utf-8")
	
	# Per TypeScript implementation: https://api-singapore.klingai.com/v1/videos/image2video
	# Note: Only kling-v2-1 (Professional) is supported by the API
	payload = {
		"model_name": "kling-v2-1",
		"duration": str(duration_seconds),
		"image": image_base64,
		"cfg_scale": cfg_scale,
		"prompt": prompt,
	}
	
	print(f"🎛️  CFG scale: {cfg_scale}")
	
	# Add negative prompt if provided
	if negative_prompt:
		payload["negative_prompt"] = negative_prompt
		print(f"🚫 Using negative prompt: {negative_prompt[:50]}...")

	url = KLING_CREATE_URL
	print(f"🔍 Debug: Kling URL: {url}")
	print(f"🔍 Debug: Payload keys: {list(payload.keys())}")
	body_str = json.dumps(payload)
	create_t0 = time.perf_counter()
	resp = requests.post(url, headers=headers, data=body_str, timeout=REQUEST_TIMEOUT_SECONDS)
	create_t2 = time.perf_counter()
	print(f"🔍 Debug: Response status: {resp.status_code}")
	print(f"🔍 Debug: Response headers: {dict(resp.headers)}")
	print(f"🔍 Debug: Response text (first 200 chars): {resp.text[:200]}")
	
	if resp.status_code >= 400:
		error_text = resp.text[:500] if len(resp.text) > 500 else resp.text
		raise RuntimeError(f"Kling create error {resp.status_code}: {error_text}")
	
	try:
		data = resp.json()
	except json.JSONDecodeError as e:
		raise RuntimeError(f"Kling response not valid JSON: {e}. Response: {resp.text[:200]}")
	
	# Per TypeScript implementation response format
	if data.get("code") != 0:
		raise RuntimeError(f"Kling API error: {data.get('message', 'Unknown error')}")
	
	if not data.get("data", {}).get("task_id"):
		raise RuntimeError(f"Kling create response missing task_id: {data}")
	
	task_id = data["data"]["task_id"]
	print(f"📋 Video generation task submitted. Task ID: {task_id}")
	create_metrics = {
		"json_body_bytes": len(body_str.encode("utf-8")),
		"create_upload_ms": 0,
		"create_ttfb_ms": int((create_t2 - create_t0) * 1000),
		"create_resp_download_ms": 0,
		"create_resp_bytes": len(resp.content or b""),
		"create_total_ms": int((create_t2 - create_t0) * 1000),
		"task_id": task_id,
	}
	return task_id, create_metrics


def kling_poll_task_result(task_id: str, *, poll_interval: float = 5.0, timeout_seconds: int = 900) -> Tuple[str, dict]:
	"""Polls Kling task until completion. Returns (downloadable video URL, poll_metrics)."""
	# Generate fresh JWT token for polling
	jwt_token = generate_kling_jwt_token()
	headers = {
		"Authorization": f"Bearer {jwt_token}",
	}
	
	url = KLING_STATUS_URL_TEMPLATE.format(task_id=task_id)
	end_time = time.time() + timeout_seconds
	attempts = 0
	max_attempts = int(timeout_seconds / poll_interval)
	
	loop_start = time.perf_counter()
	while attempts < max_attempts:
		if time.time() > end_time:
			raise TimeoutError(f"Kling task {task_id} timed out")
		
		print(f"⏳ Polling task status (attempt {attempts + 1}/{max_attempts})...")
		
		try:
			resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
			if resp.status_code >= 400:
				raise RuntimeError(f"Kling poll error {resp.status_code}: {resp.text}")
			
			data = resp.json()
			
			# Per TypeScript implementation response format
			if data.get("code") != 0:
				raise RuntimeError(f"Failed to get task status: {data.get('message', 'Unknown error')}")
			
			task_data = data.get("data", {})
			task_status = task_data.get("task_status")
			print(f"📊 Task status: {task_status}")
			
			if task_status == "succeed":
				print("✅ Task completed successfully!")
				task_result = task_data.get("task_result", {})
				videos = task_result.get("videos", [])
				
				if not videos:
					raise RuntimeError("No videos found in successful task result")
				
				video_url = videos[0].get("url")
				if not video_url:
					raise RuntimeError("No video URL found in task result")
				
				print(f"🎬 Video ready: {video_url}")
				poll_metrics = {
					"poll_attempts": attempts + 1,
					"poll_seconds": int((time.perf_counter() - loop_start)),
				}
				return video_url, poll_metrics
			
			elif task_status == "failed":
				error_msg = task_data.get("task_status_msg", "Unknown error")
				raise RuntimeError(f"Task failed: {error_msg}")
			
			elif task_status in ["submitted", "processing"]:
				print(f"⏱️ Task is {task_status}, waiting {poll_interval} seconds...")
				time.sleep(poll_interval)
				attempts += 1
			else:
				raise RuntimeError(f"Unknown task status: {task_status}")
				
		except Exception as e:
			print(f"Error polling task status (attempt {attempts + 1}): {e}")
			attempts += 1
			if attempts >= max_attempts:
				raise RuntimeError("Task polling timeout - maximum attempts reached")
			time.sleep(poll_interval)
	
	raise TimeoutError("Task polling timeout - maximum attempts reached")


# ------------------------- Google Veo 3: image-to-video -------------------------

def veo_generate_video(image_png_bytes: bytes, prompt: str, save_path: str, *, poll_interval: float = 10.0, timeout_seconds: int = 600) -> dict:
	"""Generate a video using Google Veo 3 with an image as first frame and save to save_path.
	Returns a metrics dict compatible with I2V_METRIC_HEADERS (best-effort).
	"""
	if not GOOGLE_API_KEY:
		raise RuntimeError("GOOGLE_API_KEY is required for Veo 3 generation")

	# Lazy import to avoid hard dependency when not used
	from google import genai  # type: ignore
	from google.genai import types  # type: ignore

	client = genai.Client(api_key=GOOGLE_API_KEY)

	# Build first frame object
	first_frame = types.Image(image_bytes=image_png_bytes, mime_type="image/png")

	print("🚀 Veo3: starting video generation operation…")
	start_time = time.perf_counter()
	
	# Wrap the API call with exponential backoff
	def _create_video():
		try:
			return client.models.generate_videos(
				model=VEO_MODEL,
				prompt=prompt,
				image=first_frame,
			)
		except Exception as e:
			# Check for rate limit errors
			if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
				print(f"⚠️ Veo3: Rate limit hit, will retry with backoff...")
			raise
	
	# Apply backoff to handle rate limits
	operation = with_backoff(_create_video)()
	print(f"📋 Veo3 operation started: {operation.name}")

	# Poll until completion
	end_deadline = time.time() + timeout_seconds
	attempts = 0
	while not getattr(operation, "done", False):
		attempts += 1
		if time.time() > end_deadline:
			raise TimeoutError("Veo 3 generation timed out")
		print(f"⏳ Veo3 polling attempt {attempts}…")
		time.sleep(poll_interval)
		operation = client.operations.get(operation)

	total_ms = int((time.perf_counter() - start_time) * 1000)
	print(f"✅ Veo3: operation completed in {total_ms/1000:.1f}s")

	# Download and save the first generated video
	videos = getattr(operation.response, "generated_videos", [])
	if not videos:
		raise RuntimeError("Veo 3 response missing generated_videos")
	video = videos[0]
	client.files.download(file=video.video)
	video.video.save(save_path)
	print(f"💾 Veo3: video saved to {save_path}")

	# Compose metrics best-effort
	video_bytes = os.path.getsize(save_path) if os.path.exists(save_path) else 0
	metrics = {
		"json_body_bytes": "",
		"create_upload_ms": 0,
		"create_ttfb_ms": total_ms,
		"create_resp_download_ms": 0,
		"create_resp_bytes": 0,
		"create_total_ms": total_ms,
		"task_id": getattr(operation, "name", ""),
		"poll_attempts": attempts,
		"poll_seconds": int(total_ms / 1000),
		"video_url": "",
		"video_ttfb_ms": 0,
		"video_resp_download_ms": 0,
		"video_total_ms": 0,
		"video_bytes": video_bytes,
		"total_end_to_end_ms": total_ms,
		"status": "ok",
		"error": "",
	}
	return metrics


# ------------------------- Workers -------------------------

def save_bytes(path: str, blob: bytes) -> None:
	ensure_dir(os.path.dirname(path))
	with open(path, "wb") as f:
		f.write(blob)


def download_file(url: str, path: str) -> None:
	ensure_dir(os.path.dirname(path))
	r = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
	r.raise_for_status()
	with open(path, "wb") as f:
		f.write(r.content)


def process_analyze_one(src_path: str, out_dir: str, prompt_path: str, model: str = ANALYSIS_MODEL, worker_id: int = 0) -> Optional[str]:
	"""Process one image: send to chat model for analysis and save .txt output."""
	print(f"🔄 Worker {worker_id}: Starting analysis for {os.path.basename(src_path)}")
	prompt_text = read_text_file(prompt_path)
	print(f"🧠 Worker {worker_id}: Sending to OpenAI model {model}...")
	func = with_backoff(openai_analyze_image)
	analysis_text = func(src_path, prompt_text, model=model)
	print(f"💾 Worker {worker_id}: Saving analysis text...")
	out_name = os.path.splitext(os.path.basename(src_path))[0] + ".txt"
	out_path = os.path.join(out_dir, out_name)
	save_bytes(out_path, analysis_text.encode("utf-8"))
	print(f"✅ Worker {worker_id}: Completed {os.path.basename(src_path)} -> {out_name}")
	return out_path


def process_anime_one(src_path: str, out_dir: str, prompts_path: str, size: str = IMAGE_SIZE, worker_id: int = 0, prompt_name: Optional[str] = None, backgrounds: Optional[List[str]] = None) -> Optional[str]:
	"""Process one image to anime style with progress logging."""
	print(f"🔄 Worker {worker_id}: Starting {os.path.basename(src_path)}")
	
	# Choose prompt (named or random)
	choices = read_named_prompts(prompts_path)
	if prompt_name:
		filtered = [p for p in choices if p[0] and p[0].lower() == prompt_name.lower()]
		if not filtered:
			raise ValueError(f"Prompt name '{prompt_name}' not found in {prompts_path}")
		_, prompt = filtered[0]
	else:
		_, prompt = random.choice(choices)
	
	# Append random background if provided
	if backgrounds:
		background = random.choice(backgrounds)
		prompt = f"{prompt} Background setting: {background}."
		print(f"🎨 Worker {worker_id}: Using prompt: {prompt[:80]}...")
		print(f"🖼️  Worker {worker_id}: Added background: {background[:60]}...")
	else:
		print(f"🎨 Worker {worker_id}: Using prompt: {prompt[:50]}...")
	
	print(f"🤖 Worker {worker_id}: Calling OpenAI API...")
	func = with_backoff(openai_generate_anime_image_bytes)
	try:
		img_bytes, metrics = func(src_path, prompt, size=size, prompt_name=(prompt_name or ""))
	except Exception as e:
		append_anime_metrics_row(out_dir, {
			"image_name": os.path.basename(src_path),
			"prompt_name": (prompt_name or ""),
			"size_param": size,
			"input_file_bytes": os.path.getsize(src_path),
			"request_body_bytes": "",
			"upload_ms": "",
			"ttfb_ms": "",
			"resp_download_ms": "",
			"resp_bytes": "",
			"result_kind": "",
			"image_bytes": "",
			"image_download_ms": "",
			"total_ms": "",
			"status": "error",
			"error": str(e)[:200],
		})
		raise
	
	print(f"💾 Worker {worker_id}: Saving result...")
	out_name = os.path.splitext(os.path.basename(src_path))[0] + "_anime.png"
	out_path = os.path.join(out_dir, out_name)
	save_bytes(out_path, img_bytes)

	# Append metrics row and echo concise summary
	append_anime_metrics_row(out_dir, metrics)
	print(
		f"📊 Worker {worker_id}: sent={metrics['input_file_bytes']}B body={metrics['request_body_bytes']}B | "
		f"upload={metrics['upload_ms']}ms ttfb={metrics['ttfb_ms']}ms resp_dl={metrics['resp_download_ms']}ms total={metrics['total_ms']}ms | "
		f"resp={metrics['resp_bytes']}B image={metrics['image_bytes']}B ({metrics['result_kind']})"
	)
	
	print(f"✅ Worker {worker_id}: Completed {os.path.basename(src_path)} -> {out_name}")
	return out_path


def process_i2i_gemini_one(src_path: str, out_dir: str, prompts_path: str, worker_id: int = 0, prompt_name: Optional[str] = None) -> Optional[str]:
	"""Gemini image editing via generate_content with image+prompt per docs: https://ai.google.dev/gemini-api/docs/image-generation"""
	if not GOOGLE_API_KEY:
		raise RuntimeError("GOOGLE_API_KEY is required for Google i2i")

	# Track total time
	total_start = time.perf_counter()
	
	# Choose prompt (named or random)
	choices = read_named_prompts(prompts_path)
	prompt: str
	if prompt_name:
		filtered = [p for p in choices if p[0] and p[0].lower() == prompt_name.lower()]
		if not filtered:
			raise ValueError(f"Prompt name '{prompt_name}' not found in {prompts_path}")
		_, prompt = filtered[0]
	else:
		_, prompt = random.choice(choices)

	print(f"🔄 (i2i) Worker {worker_id}: Starting {os.path.basename(src_path)}")
	from google import genai  # type: ignore
	from google.genai import types  # type: ignore

	# Get input file info
	input_file_bytes = os.path.getsize(src_path)
	
	# Load source image and prepare a PIL Image to pass to contents (per docs)
	with Image.open(src_path) as img:
		input_w, input_h = img.size
		if img.mode in ('RGBA', 'LA', 'P'):
			img = img.convert('RGB')
		img.thumbnail((1536, 1536), Image.Resampling.LANCZOS)
		pil_image = img.copy()

	client = genai.Client(api_key=GOOGLE_API_KEY)
	
	# Track API call time
	api_start = time.perf_counter()
	
	# Per docs, pass contents with prompt and image; get inline_data back
	print(f"🤖 (i2i) Worker {worker_id}: Calling Google {GOOGLE_GEMINI_IMAGE_MODEL} generate_content…")
	try:
		resp = client.models.generate_content(
			model=GOOGLE_GEMINI_IMAGE_MODEL,
			contents=[prompt, pil_image],
		)
		api_end = time.perf_counter()
		request_time_ms = int((api_end - api_start) * 1000)
		
		# Extract first inline image
		bytes_out: Optional[bytes] = None
		for cand in getattr(resp, 'candidates', []) or []:
			content = getattr(cand, 'content', None)
			if not content:
				continue
			for part in getattr(content, 'parts', []) or []:
				if getattr(part, 'inline_data', None) and getattr(part.inline_data, 'data', None):
					bytes_out = part.inline_data.data
					break
			if bytes_out:
				break
		if not bytes_out:
			raise RuntimeError("Google i2i returned no inline image data")

		# Save bytes from response
		out_name = os.path.splitext(os.path.basename(src_path))[0] + "_gemini.png"
		out_path = os.path.join(out_dir, out_name)
		ensure_dir(out_dir)
		save_bytes(out_path, bytes_out)
		
		# Get output image dimensions
		try:
			with Image.open(out_path) as out_img:
				output_w, output_h = out_img.size
		except Exception:
			output_w, output_h = ("", "")
		
		# Calculate total time
		total_end = time.perf_counter()
		total_time_ms = int((total_end - total_start) * 1000)
		
		# Log metrics
		metrics = {
			"image_name": os.path.basename(src_path),
			"prompt_name": prompt_name or "",
			"input_file_bytes": input_file_bytes,
			"input_px_w": input_w,
			"input_px_h": input_h,
			"request_time_ms": request_time_ms,
			"response_bytes": len(bytes_out),
			"output_px_w": output_w,
			"output_px_h": output_h,
			"total_time_ms": total_time_ms,
			"status": "ok",
			"error": "",
		}
		append_gemini_i2i_metrics_row(out_dir, metrics)
		
		print(f"📊 (i2i) Worker {worker_id}: input={input_file_bytes}B ({input_w}x{input_h}) | "
			  f"request={request_time_ms}ms | output={len(bytes_out)}B ({output_w}x{output_h}) | "
			  f"total={total_time_ms}ms")
		print(f"✅ (i2i) Worker {worker_id}: Completed {os.path.basename(src_path)} -> {out_name}")
		return out_path
		
	except Exception as e:
		# Log error metrics
		total_end = time.perf_counter()
		total_time_ms = int((total_end - total_start) * 1000)
		
		metrics = {
			"image_name": os.path.basename(src_path),
			"prompt_name": prompt_name or "",
			"input_file_bytes": input_file_bytes,
			"input_px_w": input_w,
			"input_px_h": input_h,
			"request_time_ms": "",
			"response_bytes": "",
			"output_px_w": "",
			"output_px_h": "",
			"total_time_ms": total_time_ms,
			"status": "error",
			"error": str(e)[:200],
		}
		append_gemini_i2i_metrics_row(out_dir, metrics)
		raise

def process_i2v_one(src_path: str, out_dir: str, prompts_path: str, duration_seconds: int = VIDEO_DURATION_SECONDS, worker_id: int = 0, prompt_name: Optional[str] = None, i2v_model: str = "kling", negative_prompt: Optional[str] = None, cfg_scale: float = 0.5, camera_directions: Optional[List[str]] = None, backgrounds: Optional[List[str]] = None, gender: Optional[str] = None) -> Optional[str]:
	"""Process one image to video with progress logging."""
	print(f"🎬 Worker {worker_id}: Starting video generation for {os.path.basename(src_path)}")
	
	# Track what was actually used for logging
	used_gender = ""
	used_camera = ""
	used_background = ""
	used_negative = "yes" if negative_prompt else "no"
	
	# Choose prompt (named or random)
	if prompt_name:
		choices_named = read_named_prompts(prompts_path)
		filtered = [p for p in choices_named if p[0] and p[0].lower() == prompt_name.lower()]
		if not filtered:
			raise ValueError(f"Prompt name '{prompt_name}' not found in {prompts_path}")
		_, prompt = filtered[0]
	else:
		prompts = read_prompts_file(prompts_path)
		prompt = random.choice(prompts)
	
	# Apply gender transformation if specified
	if gender and gender.upper() in ["M", "F"]:
		used_gender = gender.upper()
		original_prompt = prompt
		prompt = genderize_prompt(prompt, gender.upper())
		print(f"⚧️  Worker {worker_id}: Applied gender transformation ({gender.upper()})")
		if len(prompt) != len(original_prompt):
			print(f"🎨 Worker {worker_id}: Genderized prompt: {prompt[:80]}...")
	
	# Append random background if provided
	if backgrounds:
		background = random.choice(backgrounds)
		used_background = background
		prompt = f"{prompt} Setting: {background}."
		print(f"🎨 Worker {worker_id}: Using prompt: {prompt[:80]}...")
		print(f"🏞️  Worker {worker_id}: Added background: {background}")
	else:
		if not gender:
			print(f"🎨 Worker {worker_id}: Using prompt: {prompt[:50]}...")
	
	# Append random camera direction if provided
	if camera_directions:
		camera_dir = random.choice(camera_directions)
		used_camera = camera_dir
		prompt = f"{prompt} {camera_dir}"
		print(f"🎥 Worker {worker_id}: Added camera direction: {camera_dir[:60]}...")
		if not backgrounds and not gender:
			print(f"🎨 Worker {worker_id}: Using prompt: {prompt[:80]}...")
	
	# Load and resize image to reduce file size; prepare JPEG (Kling) and PNG (Veo3)
	print(f"📁 Worker {worker_id}: Loading and resizing image...")
	with Image.open(src_path) as img:
		# Convert to RGB if needed
		if img.mode in ('RGBA', 'LA', 'P'):
			img = img.convert('RGB')
		# Resize to max 1024x1024 to reduce file size
		img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
		# Capture dimensions
		in_w, in_h = img.size
		# JPEG bytes for Kling
		jpeg_buf = BytesIO()
		img.save(jpeg_buf, format='JPEG', quality=85, optimize=True)
		img_bytes_jpeg = jpeg_buf.getvalue()
		# PNG bytes for Veo3
		png_buf = BytesIO()
		img.save(png_buf, format='PNG', optimize=True)
		img_bytes_png = png_buf.getvalue()

	print(f"📏 Worker {worker_id}: Image sizes jpeg={len(img_bytes_jpeg)}B png={len(img_bytes_png)}B")

	out_name = os.path.splitext(os.path.basename(src_path))[0] + ".mp4"
	out_path = os.path.join(out_dir, out_name)

	if (i2v_model or "kling").lower() == "veo3":
		print(f"🤖 Worker {worker_id}: Using Google Veo 3 ({VEO_MODEL})")
		try:
			metrics = veo_generate_video(img_bytes_png, prompt, out_path)
			row = {
				"image_name": os.path.basename(src_path),
				"prompt_name": prompt_name or "",
				"duration_seconds": duration_seconds,
				"input_px_w": in_w,
				"input_px_h": in_h,
				"input_image_bytes": len(img_bytes_png),
				**metrics,
			}
			append_i2v_metrics_row(out_dir, row)
			print(f"✅ Worker {worker_id}: Completed {os.path.basename(src_path)} -> {out_name}")
			return out_path
		except Exception as e:
			append_i2v_metrics_row(out_dir, {
				"image_name": os.path.basename(src_path),
				"prompt_name": prompt_name or "",
				"duration_seconds": duration_seconds,
				"input_px_w": in_w,
				"input_px_h": in_h,
				"input_image_bytes": len(img_bytes_png),
				"status": "error",
				"error": str(e)[:200],
			})
			raise
	else:
		print(f"🤖 Worker {worker_id}: Using Kling API")
		print(f"🚀 Worker {worker_id}: Creating Kling task...")
		create_with_backoff = with_backoff(kling_create_i2v_task)
		poll_with_backoff = with_backoff(kling_poll_task_result)
		create_result = create_with_backoff(img_bytes_jpeg, prompt, duration_seconds=duration_seconds, negative_prompt=negative_prompt, cfg_scale=cfg_scale)
		if isinstance(create_result, tuple):
			task_id, create_metrics = create_result
		else:
			# backward compat
			task_id, create_metrics = create_result, {"json_body_bytes": "", "create_upload_ms": "", "create_ttfb_ms": "", "create_resp_download_ms": "", "create_resp_bytes": "", "create_total_ms": "", "task_id": task_id}
		print(f"⏳ Worker {worker_id}: Task created {task_id}, polling for completion...")
		
		poll_result = poll_with_backoff(task_id)
		if isinstance(poll_result, tuple):
			video_url, poll_metrics = poll_result
		else:
			video_url, poll_metrics = poll_result, {"poll_attempts": "", "poll_seconds": ""}
		print(f"📥 Worker {worker_id}: Video ready, downloading...")
		
		# Measure video download timing and size
		vid_t0 = time.perf_counter()
		resp = requests.get(video_url, timeout=REQUEST_TIMEOUT_SECONDS)
		resp.raise_for_status()
		vid_t2 = time.perf_counter()
		video_bytes = len(resp.content)
		with open(out_path, "wb") as vf:
			vf.write(resp.content)
		
		# Compose and append metrics
		row = {
			"image_name": os.path.basename(src_path),
			"prompt_name": prompt_name or "",
			"actual_prompt": prompt[:200] if len(prompt) <= 200 else prompt[:197] + "...",
			"gender": used_gender,
			"camera_direction": used_camera[:100] if used_camera else "",
			"background": used_background[:100] if used_background else "",
			"negative_prompt_used": used_negative,
			"cfg_scale": cfg_scale,
			"duration_seconds": duration_seconds,
			"input_px_w": in_w,
			"input_px_h": in_h,
			"input_image_bytes": len(img_bytes_jpeg),
			**create_metrics,
			**poll_metrics,
			"video_url": video_url,
			"video_ttfb_ms": 0,
			"video_resp_download_ms": int((vid_t2 - vid_t0) * 1000),
			"video_total_ms": int((vid_t2 - vid_t0) * 1000),
			"video_bytes": video_bytes,
			"total_end_to_end_ms": int((vid_t2 - vid_t0) * 1000) + (create_metrics.get("create_total_ms", 0) or 0),
			"status": "ok",
			"error": "",
		}
		append_i2v_metrics_row(out_dir, row)
		
		print(f"✅ Worker {worker_id}: Completed {os.path.basename(src_path)} -> {out_name}")
		return out_path


# ------------------------- CLI -------------------------

def run_anime(args: argparse.Namespace) -> None:
	files = list_images(args.input)
	if not files:
		print("No images found.")
		return
	ensure_dir(args.output)
	# Create unique run output directory
	out_dir = make_unique_output_dir(args.output)
	
	# Load backgrounds if requested
	backgrounds = None
	if args.use_backgrounds:
		try:
			backgrounds = read_prompts_file(args.backgrounds_file)
			print(f"🖼️  Using backgrounds from: {args.backgrounds_file}")
			print(f"   Loaded {len(backgrounds)} backgrounds")
		except FileNotFoundError:
			print(f"⚠️  Warning: Backgrounds file not found: {args.backgrounds_file}")
			print(f"   Continuing without backgrounds...")
	
	workers = max(1, min(args.workers, ANIME_MAX_WORKERS))
	print(f"🎨 Anime: processing {len(files)} images with up to {workers} workers (cap {ANIME_MAX_WORKERS})…")
	print(f"📁 Output: {out_dir}")
	
	# Check if there's a linked i2v style for this i2i style
	if args.prompt_name:
		linked_i2v = get_linked_i2v_style(args.prompt_name)
		if linked_i2v:
			print(f"🔗 Style '{args.prompt_name}' is linked to i2v style '{linked_i2v}'")
			print(f"   💡 Recommended i2v command:")
			print(f"   python src/batch_media.py i2v --input {out_dir} --output outputs/videos \\")
			print(f"      --prompts prompts/kling_prompts.txt --prompt-name {linked_i2v} --workers 20")
	
	# Create progress bar
	pbar = tqdm(total=len(files), desc="Anime conversion", unit="image")
	
	with ThreadPoolExecutor(max_workers=workers) as ex:
		# Submit all tasks with worker IDs
		futures = {}
		for i, p in enumerate(files):
			fut = ex.submit(process_anime_one, p, out_dir, args.prompts, args.size, i, args.prompt_name, backgrounds)
			futures[fut] = (p, i)
		
		# Process completed tasks
		for fut in as_completed(futures):
			src, worker_id = futures[fut]
			try:
				res = fut.result()
				if res:
					pbar.set_postfix_str(f"✅ {os.path.basename(src)}")
				else:
					pbar.set_postfix_str(f"❌ {os.path.basename(src)}")
			except Exception as e:
				pbar.set_postfix_str(f"❌ {os.path.basename(src)}: {str(e)[:30]}...")
			finally:
				pbar.update(1)
	
	pbar.close()
	print(f"🎉 Anime conversion complete! Check {out_dir} for results.")


def run_i2i_gemini(args: argparse.Namespace) -> None:
	files = list_images(args.input)
	if not files:
		print("No images found.")
		return
	ensure_dir(args.output)
	# Create unique run output directory
	out_dir = make_unique_output_dir(args.output)
	workers = max(1, min(args.workers, ANIME_MAX_WORKERS))
	print(f"🖼️  Google i2i: processing {len(files)} images with up to {workers} workers (cap {ANIME_MAX_WORKERS})…")
	print(f"📁 Output: {out_dir}")

	pbar = tqdm(total=len(files), desc="Google i2i", unit="image")
	with ThreadPoolExecutor(max_workers=workers) as ex:
		futures = {}
		for i, p in enumerate(files):
			fut = ex.submit(process_i2i_gemini_one, p, out_dir, args.prompts, i, args.prompt_name)
			futures[fut] = (p, i)
		for fut in as_completed(futures):
			src, worker_id = futures[fut]
			try:
				res = fut.result()
				if res:
					pbar.set_postfix_str(f"✅ {os.path.basename(src)}")
				else:
					pbar.set_postfix_str(f"❌ {os.path.basename(src)}")
			except Exception as e:
				pbar.set_postfix_str(f"❌ {os.path.basename(src)}: {str(e)[:30]}...")
			finally:
				pbar.update(1)
	
	pbar.close()
	print(f"🎉 Google i2i complete! Check {out_dir} for results.")


def run_i2v(args: argparse.Namespace) -> None:
	files = list_images(args.input)
	if not files:
		print("No images found.")
		return
	ensure_dir(args.output)
	# Create unique run output directory
	out_dir = make_unique_output_dir(args.output)
	
	# Load negative prompt if requested
	negative_prompt = None
	if args.use_negative_prompt:
		try:
			with open(args.negative_prompt_file, 'r', encoding='utf-8') as f:
				negative_prompt = f.read().strip()
			print(f"🚫 Using negative prompt from: {args.negative_prompt_file}")
			print(f"   Content: {negative_prompt}")
		except FileNotFoundError:
			print(f"⚠️  Warning: Negative prompt file not found: {args.negative_prompt_file}")
			print(f"   Continuing without negative prompt...")
	
	# Load backgrounds if requested
	backgrounds = None
	if args.use_i2v_backgrounds:
		try:
			with open(args.i2v_backgrounds_file, 'r', encoding='utf-8') as f:
				backgrounds = [line.strip() for line in f if line.strip()]
			print(f"🏞️  Using backgrounds from: {args.i2v_backgrounds_file}")
			print(f"   Loaded {len(backgrounds)} backgrounds")
		except FileNotFoundError:
			print(f"⚠️  Warning: Backgrounds file not found: {args.i2v_backgrounds_file}")
			print(f"   Continuing without backgrounds...")
	
	# Load camera directions if requested
	camera_directions = None
	if args.use_camera_directions:
		try:
			camera_directions_named = read_named_prompts(args.camera_directions_file)
			
			# Filter by category if specified
			if args.camera_category:
				category_prefix = args.camera_category.lower()
				camera_directions_named = [(name, direction) for name, direction in camera_directions_named 
				                            if name.lower().startswith(category_prefix)]
				if not camera_directions_named:
					print(f"⚠️  Warning: No camera directions found matching category '{args.camera_category}'")
					print(f"   Continuing without camera directions...")
				else:
					print(f"🎥 Using camera directions from: {args.camera_directions_file}")
					print(f"   Filtered by category: {args.camera_category}")
					print(f"   Loaded {len(camera_directions_named)} camera directions")
			
			# Further filter by number range if specified
			if args.camera_range and camera_directions_named:
				try:
					range_parts = args.camera_range.split('-')
					if len(range_parts) == 2:
						min_num = int(range_parts[0])
						max_num = int(range_parts[1])
						# Extract number from name (e.g., "cutbased8" -> 8)
						filtered = []
						for name, direction in camera_directions_named:
							# Extract trailing digits
							import re
							match = re.search(r'(\d+)$', name)
							if match:
								num = int(match.group(1))
								if min_num <= num <= max_num:
									filtered.append((name, direction))
						camera_directions_named = filtered
						if not camera_directions_named:
							print(f"⚠️  Warning: No camera directions found in range {args.camera_range}")
							print(f"   Continuing without camera directions...")
						else:
							print(f"   Further filtered by range: {args.camera_range}")
							print(f"   Final count: {len(camera_directions_named)} camera directions")
				except (ValueError, IndexError):
					print(f"⚠️  Warning: Invalid range format '{args.camera_range}'. Use format '8-14'")
			
			if not args.camera_category and not args.camera_range:
				print(f"🎥 Using camera directions from: {args.camera_directions_file}")
				print(f"   Loaded {len(camera_directions_named)} camera directions")
			
			# Extract just the direction text (not the names)
			camera_directions = [direction for _, direction in camera_directions_named] if camera_directions_named else None
		except FileNotFoundError:
			print(f"⚠️  Warning: Camera directions file not found: {args.camera_directions_file}")
			print(f"   Continuing without camera directions...")
	
	# Use model-specific worker limits
	if args.model == "kling":
		max_workers_cap = KLING_MAX_WORKERS
	else:
		max_workers_cap = I2V_MAX_WORKERS
	workers = max(1, min(args.workers, max_workers_cap))
	print(f"🎬 i2v ({args.model}): processing {len(files)} images with up to {workers} workers (cap {max_workers_cap})…")
	print(f"📁 Output: {out_dir}")
	
	# Create progress bar
	pbar = tqdm(total=len(files), desc="Video generation", unit="video")
	
	# Get gender parameter if specified
	gender = getattr(args, 'gender', None)
	if gender:
		print(f"⚧️  Using gender transformation: {gender.upper()}")
	
	with ThreadPoolExecutor(max_workers=workers) as ex:
		# Submit all tasks with worker IDs
		futures = {}
		for i, p in enumerate(files):
			fut = ex.submit(process_i2v_one, p, out_dir, args.prompts, args.duration, i, args.prompt_name, args.model, negative_prompt, args.cfg_scale, camera_directions, backgrounds, gender)
			futures[fut] = (p, i)
		
		# Process completed tasks
		for fut in as_completed(futures):
			src, worker_id = futures[fut]
			try:
				res = fut.result()
				if res:
					pbar.set_postfix_str(f"✅ {os.path.basename(src)}")
				else:
					pbar.set_postfix_str(f"❌ {os.path.basename(src)}")
			except Exception as e:
				pbar.set_postfix_str(f"❌ {os.path.basename(src)}: {str(e)[:30]}...")
			finally:
				pbar.update(1)
	
	pbar.close()
	print(f"🎉 Video generation complete! Check {out_dir} for results.")


def run_analyze(args: argparse.Namespace) -> None:
	files = list_images(args.input)
	if not files:
		print("No images found.")
		return
	ensure_dir(args.output)
	workers = max(1, min(args.workers, MAX_WORKERS))
	print(f"🧪 Analyze: processing {len(files)} images with up to {workers} workers (cap {MAX_WORKERS})…")

	# Progress bar
	pbar = tqdm(total=len(files), desc="Image analysis", unit="image")

	with ThreadPoolExecutor(max_workers=workers) as ex:
		futures = {}
		for i, p in enumerate(files):
			fut = ex.submit(process_analyze_one, p, args.output, args.prompts, args.model, i)
			futures[fut] = (p, i)
		for fut in as_completed(futures):
			src, worker_id = futures[fut]
			try:
				res = fut.result()
				if res:
					pbar.set_postfix_str(f"✅ {os.path.basename(src)}")
				else:
					pbar.set_postfix_str(f"❌ {os.path.basename(src)}")
			except Exception as e:
				pbar.set_postfix_str(f"❌ {os.path.basename(src)}: {str(e)[:30]}...")
			finally:
				pbar.update(1)

	pbar.close()
	print(f"🎉 Analysis complete! Check {args.output} for results.")


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Batch media: anime (OpenAI) and i2v (Kling)")
	sub = parser.add_subparsers(dest="cmd", required=True)

	p_anime = sub.add_parser("anime", help="Stylize images to anime via OpenAI gpt-image-1")
	p_anime.add_argument("--input", required=True, help="Input images directory")
	p_anime.add_argument("--output", required=True, help="Output directory for anime images")
	p_anime.add_argument("--prompts", required=True, help="Path to anime prompts text file")
	p_anime.add_argument("--workers", type=int, default=ANIME_MAX_WORKERS, help=f"Max parallel workers (default {ANIME_MAX_WORKERS}, cap {ANIME_MAX_WORKERS})")
	p_anime.add_argument("--size", default=IMAGE_SIZE, help="OpenAI image size, e.g., 1024x1024 or auto (default: auto)")
	p_anime.add_argument("--prompt-name", help="Select a named prompt from the prompts file (format: name: prompt)")
	p_anime.add_argument("--use-backgrounds", action="store_true", help="Randomly append backgrounds to prompts")
	p_anime.add_argument("--backgrounds-file", default="prompts/i2i_backgrounds.txt", help="Path to backgrounds file (default: prompts/i2i_backgrounds.txt)")
	p_anime.set_defaults(func=run_anime)

	# Google i2i subcommand
	p_i2i = sub.add_parser("i2i", help="Image-to-image via Google (Imagen/Gemini)")
	p_i2i.add_argument("--input", required=True, help="Input images directory")
	p_i2i.add_argument("--output", required=True, help="Output directory for stylized images")
	p_i2i.add_argument("--prompts", required=True, help="Path to i2i prompts text file")
	p_i2i.add_argument("--workers", type=int, default=ANIME_MAX_WORKERS, help=f"Max parallel workers (default {ANIME_MAX_WORKERS}, cap {ANIME_MAX_WORKERS})")
	p_i2i.add_argument("--prompt-name", help="Select a named prompt from the prompts file (format: name: prompt)")
	p_i2i.set_defaults(func=run_i2i_gemini)

	p_i2v = sub.add_parser("i2v", help="Convert images to video via Kling or Google Veo 3")
	p_i2v.add_argument("--input", required=True, help="Input images directory")
	p_i2v.add_argument("--output", required=True, help="Output directory for videos")
	p_i2v.add_argument("--prompts", required=True, help="Path to i2v prompts text file")
	p_i2v.add_argument("--workers", type=int, default=I2V_MAX_WORKERS, help=f"Max parallel workers (default {I2V_MAX_WORKERS}, cap {I2V_MAX_WORKERS})")
	p_i2v.add_argument("--duration", type=int, default=VIDEO_DURATION_SECONDS, help="Video duration seconds (5 or 10)")
	p_i2v.add_argument("--prompt-name", help="Select a named prompt from the prompts file (format: name: prompt)")
	p_i2v.add_argument("--model", choices=["kling", "veo3"], default=I2V_MODEL, help="i2v model/provider to use: kling or veo3 (default from I2V_MODEL)")
	p_i2v.add_argument("--cfg-scale", type=float, default=0.5, help="CFG scale for prompt adherence (0.0-1.0, Kling only). Higher = stricter. Default: 0.5")
	p_i2v.add_argument("--use-negative-prompt", action="store_true", help="Use negative prompt from prompts/i2v_negative_prompt.txt (Kling only)")
	p_i2v.add_argument("--negative-prompt-file", default="prompts/i2v_negative_prompt.txt", help="Path to negative prompt file (default: prompts/i2v_negative_prompt.txt)")
	p_i2v.add_argument("--use-i2v-backgrounds", action="store_true", help="Randomly append backgrounds to i2v prompts")
	p_i2v.add_argument("--i2v-backgrounds-file", default="prompts/i2i_backgrounds.txt", help="Path to backgrounds file (default: prompts/i2i_backgrounds.txt)")
	p_i2v.add_argument("--use-camera-directions", action="store_true", help="Randomly append camera directions to prompts")
	p_i2v.add_argument("--camera-directions-file", default="prompts/i2v_camera_directions.txt", help="Path to camera directions file (default: prompts/i2v_camera_directions.txt)")
	p_i2v.add_argument("--camera-category", help="Filter camera directions by category prefix (e.g., 'smooth', 'rhythm', 'energetic', 'cutbased')")
	p_i2v.add_argument("--camera-range", help="Filter by number range (e.g., '8-14' for cutbased8 through cutbased14)")
	p_i2v.add_argument("--gender", choices=["M", "F", "m", "f"], help="Apply gender presentation transformation: M (masculine) or F (feminine)")
	p_i2v.set_defaults(func=run_i2v)

	# Analyze subcommand
	p_analyze = sub.add_parser("analyze", help="Analyze images with an OpenAI chat model using a template prompt")
	p_analyze.add_argument("--input", required=True, help="Input images directory")
	p_analyze.add_argument("--output", required=True, help="Output directory for analysis text files")
	p_analyze.add_argument("--prompts", required=True, help="Path to analysis template prompt text file")
	p_analyze.add_argument("--workers", type=int, default=MAX_WORKERS, help=f"Max parallel workers (default {MAX_WORKERS}, cap {MAX_WORKERS})")
	p_analyze.add_argument("--model", default=ANALYSIS_MODEL, help="OpenAI analysis model (default from ANALYSIS_MODEL)")
	p_analyze.set_defaults(func=run_analyze)

	return parser


def main(argv: Optional[List[str]] = None) -> int:
	parser = build_parser()
	args = parser.parse_args(argv)
	args.func(args)
	return 0


if __name__ == "__main__":
	sys.exit(main())
