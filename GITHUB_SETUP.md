# GitHub Setup Guide - Keeping API Keys Safe

## ✅ Pre-Push Checklist

Before pushing to GitHub, verify:

1. **No `.env` file exists** (or it's in `.gitignore`)
2. **No API keys hardcoded** in source files
3. **`.gitignore` includes** `.env` and sensitive files
4. **`env.example` exists** as a template (without real keys)

## Step-by-Step: Push to GitHub Safely

### 1. Verify Your `.gitignore` is Working

```bash
# Check if .env is ignored
git status

# If .env shows up, it's NOT ignored - fix .gitignore first!
```

### 2. Check for Accidental API Key Commits

```bash
# Search for potential secrets in tracked files
git grep -i "api.*key" -- "*.py" "*.md" "*.txt"
git grep -i "sk-" -- "*.py" "*.md" "*.txt"  # OpenAI/Groq keys start with sk-
```

### 3. Create `.env` File Locally (If Not Exists)

```bash
# Copy the example
cp env.example .env

# Edit .env with your actual keys (this file is gitignored)
# Use your preferred editor
```

### 4. Stage and Commit Files

```bash
# Add all files (except those in .gitignore)
git add .

# Verify what's being committed
git status

# Commit
git commit -m "Initial commit: Agentic Chatbot FastAPI project"
```

### 5. Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (don't initialize with README if you already have one)
3. Copy the repository URL

### 6. Push to GitHub

```bash
# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/your-repo-name.git

# Push
git push -u origin main
# or if your default branch is master:
git push -u origin master
```

## 🔒 Security Verification

After pushing, verify:

1. **Check GitHub**: Visit your repo and confirm `.env` is NOT visible
2. **Check `.gitignore`**: Should be visible and include `.env`
3. **Check `env.example`**: Should be visible as a template

## 🚨 If You Accidentally Committed Secrets

**IMMEDIATELY:**

1. **Rotate your API keys** - Generate new ones from the provider
2. **Remove from Git history**:
   ```bash
   # Remove file from history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push (WARNING: This rewrites history)
   git push origin --force --all
   ```
3. **Update `.gitignore`** to prevent future commits
4. **Notify team members** if working in a team

## 📝 Best Practices

- ✅ Always use environment variables
- ✅ Never commit `.env` files
- ✅ Use `env.example` as documentation
- ✅ Review `git diff` before committing
- ✅ Use GitHub's secret scanning (enabled by default)
- ✅ Consider using GitHub Secrets for CI/CD

## 🔍 Quick Security Check Script

Run this before every commit:

```bash
# Check for common secret patterns
grep -r "sk-[a-zA-Z0-9]" --include="*.py" --exclude-dir=.git .
grep -r "api[_-]key.*=.*['\"][^'\"]" --include="*.py" --exclude-dir=.git .
```

If any results appear, **DO NOT COMMIT** - fix the code first!

