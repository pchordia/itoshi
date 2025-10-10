# Archived Files

This folder contains files that are no longer actively used in the project but are kept for reference.

## 📦 Contents

### `web_app_and_deployment/`
Web application and deployment configuration files.

**Includes:**
- Flask web application code and assets
- Deployment guides (AWS EC2, Railway, Render, Heroku)
- Server configuration files (nginx, supervisor, gunicorn)
- macOS desktop app files
- Deployment scripts and configurations

**Why archived:** Web app prototype no longer actively maintained. Core functionality moved to CLI tools.

**See:** `web_app_and_deployment/README.md` for detailed contents.

### `misc_exports/`
One-time exports and data snapshots.

**Includes:**
- `i2i_claymation_to_antiquepuppetcreepy.csv` - Export of i2i prompt styles
- `i2v_last_4_prompts.csv` - Export of i2v prompt styles

**Why archived:** One-time exports for sharing. Prompts are maintained in `prompts/` folder.

## 🔍 When to Use Archived Files

### Use archived files when:
- ✅ You need to reference past deployment strategies
- ✅ You want to restore the web app functionality
- ✅ You need examples of server configurations
- ✅ You're looking for historical documentation

### Don't use archived files for:
- ❌ Current project development (use `src/` instead)
- ❌ Active deployment (may be outdated)
- ❌ Production use (needs updating first)

## 📝 Best Practices

1. **Check dates** - Files may be outdated
2. **Update dependencies** - Check `requirements.txt` for current versions
3. **Test thoroughly** - Archived code may not work with current APIs
4. **Document changes** - If you restore something, document what you updated

## 🗂️ File Organization

```
archived/
├── README.md (this file)
├── web_app_and_deployment/
│   ├── README.md
│   ├── WEB_APP_*.md
│   ├── DEPLOYMENT_*.md
│   ├── deploy/
│   ├── app/
│   └── [config files]
└── misc_exports/
    └── *.csv
```

## ⚠️ Important Notes

- **Not production-ready** - These files need review and updating before use
- **Dependencies may be outdated** - Check and update all dependencies
- **API changes** - OpenAI and Kling APIs may have changed
- **Security** - Review all security configurations before deploying

## 🚀 Restoring from Archive

If you need to restore any archived component:

1. **Review the README** in the specific folder
2. **Check dependencies** against current project
3. **Update configurations** for current environment
4. **Test locally** before deploying
5. **Document changes** you make

## 📧 Questions?

Refer to the main project `README.md` or specific archived component READMEs for more information.

---

**Created:** October 2025  
**Purpose:** Historical reference and documentation  
**Status:** Not actively maintained



