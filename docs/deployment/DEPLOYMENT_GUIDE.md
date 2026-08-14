# Databricks App Deployment Guide

A complete guide for forking, modifying, and deploying Databricks Apps from GitHub repositories you don't own.

---

## 🔐 Security Note: GitHub Personal Access Tokens

**IMPORTANT:** GitHub Personal Access Tokens are **NOT single-use**. They remain valid until:
- They expire (if you set an expiration date when creating them)
- You manually revoke them

**Best Practice:** After using a token, revoke it immediately and create a new one for future use.

### How to Revoke a Token
1. Go to https://github.com/settings/tokens
2. Find the token you used
3. Click **"Delete"** or **"Revoke"**
4. Create a new token only when you need it next time

---

## 📋 Complete Deployment Process

### **Situation**
You want to modify a Databricks App deployed from someone else's GitHub repository (you don't have push access to the original repo).

### **Solution Overview**
1. Create your own GitHub repository
2. Copy and modify the app files locally
3. Push to your repository
4. Update Databricks App configuration
5. Deploy with your changes

---

## Step-by-Step Instructions

### **Step 1: Create Your Own GitHub Repository**

1. Go to https://github.com/new
2. Repository name: Choose a descriptive name (e.g., `my-stock-app`, `databricks-lakebase-app`)
3. **Important:** Do NOT initialize with README, .gitignore, or license (we already have these files)
4. Click **"Create repository"**
5. **Copy the repository URL** (looks like `https://github.com/YOUR_USERNAME/repo-name.git`)

---

### **Step 2: Set Up Local Workspace**

In a Databricks notebook cell or workspace terminal:

```bash
# Navigate to your workspace home
cd /Workspace/Users/YOUR_EMAIL

# Create a fresh directory for your app
mkdir my-app-name
cd my-app-name

# Initialize git repository
git init

# Rename branch to main (if needed)
git branch -m main

# Configure git user (required for commits)
git config user.email "your-email@example.com"
git config user.name "Your Name"
```

---

### **Step 3: Copy Files from Original App**

```bash
# Copy all files from the original app directory
# Replace /path/to/original/app with the actual path
cp -r /path/to/original/app/* .

# Verify files were copied
ls -la

# You should see: app.py, app.yaml, templates/, requirements.txt, etc.
```

---

### **Step 4: Make Your Modifications**

Now edit the files as needed:

```bash
# Edit app.py for backend changes
# Edit templates/index.html for UI changes
# Update README.md with your changes
# Modify requirements.txt if you added dependencies
```

**Example modifications:**
- Improve UI/UX in `templates/index.html`
- Add new API endpoints in `app.py`
- Add new features or functionality
- Fix bugs or issues

---

### **Step 5: Commit Your Changes**

```bash
# Check what files you have
git status

# Stage all files
git add .

# Verify what will be committed
git status

# Commit with a descriptive message
git commit -m "Initial commit: Modified app with improvements"

# Verify commit was created
git log -1 --oneline
```

---

### **Step 6: Add GitHub Remote**

```bash
# Add your GitHub repository as the remote
git remote add origin https://github.com/YOUR_USERNAME/your-repo.git

# Verify remote was added
git remote -v

# You should see:
# origin  https://github.com/YOUR_USERNAME/your-repo.git (fetch)
# origin  https://github.com/YOUR_USERNAME/your-repo.git (push)
```

---

### **Step 7: Create GitHub Personal Access Token**

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Token name: `Databricks App Deployment`
4. Expiration: Choose 30 days or custom
5. **Scopes:** Check the **"repo"** checkbox (full control of repositories)
6. Scroll down and click **"Generate token"**
7. **IMMEDIATELY COPY THE TOKEN** - you won't see it again!
   - Token format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### **Step 8: Push to GitHub**

**Method 1: Inline Token (Recommended for Databricks)**

In a notebook cell with `%%sh`:

```bash
cd /Workspace/Users/YOUR_EMAIL/my-app-name

# Push using token in URL
git push https://YOUR_GITHUB_TOKEN@github.com/YOUR_USERNAME/your-repo.git main
```

**Method 2: Interactive (if terminal supports credential prompts)**

```bash
git push origin main

# When prompted:
# Username: YOUR_GITHUB_USERNAME
# Password: YOUR_GITHUB_TOKEN (paste the token, not your GitHub password)
```

**Verify Push Succeeded:**
- Check https://github.com/YOUR_USERNAME/your-repo
- You should see all your files listed

---

### **Step 9: Update Databricks App Configuration**

Now tell your Databricks App to use your new repository instead of the original.

**Option A: Using Databricks CLI**

```bash
# Update app source
databricks apps update YOUR_APP_NAME \
  --source-code-path https://github.com/YOUR_USERNAME/your-repo

# Deploy the updated app
databricks apps deploy YOUR_APP_NAME

# Check deployment status
databricks apps get YOUR_APP_NAME
```

**Option B: Using Databricks UI**

1. Go to your Databricks workspace
2. Navigate to **Workspace → Apps**
3. Click on your app name
4. Click **"Settings"** or **"Configure"**
5. Find **Git Repository** or **Source Code** section
6. Update the URL to: `https://github.com/YOUR_USERNAME/your-repo`
7. Select branch: `main`
8. Click **"Save"**
9. Click **"Deploy"** or **"Redeploy"**

---

### **Step 10: Security Cleanup**

**IMPORTANT:** After successful push, revoke your token:

1. Go to https://github.com/settings/tokens
2. Find the token you just created
3. Click **"Delete"** or **"Revoke"**
4. Confirm deletion

**Why?** 
- Tokens exposed in logs or history remain valid
- Revoking prevents unauthorized access
- Create a fresh token next time you need to push

---

## 🔄 Future Updates Workflow

When you need to make more changes:

```bash
# Navigate to your app directory
cd /Workspace/Users/YOUR_EMAIL/my-app-name

# Make your changes to files
# (edit app.py, templates/index.html, etc.)

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Create a new GitHub token (previous one should be revoked)
# Then push with the new token
git push https://NEW_TOKEN@github.com/YOUR_USERNAME/your-repo.git main

# Redeploy app (it may auto-deploy, or use CLI/UI)
databricks apps deploy YOUR_APP_NAME

# Revoke the token after push
```

---

## 🛠️ Troubleshooting

### Problem: "fatal: not a git repository"
**Solution:** You're not in the git directory. Navigate to your app folder:
```bash
cd /Workspace/Users/YOUR_EMAIL/my-app-name
```

### Problem: "remote origin already exists"
**Solution:** Update the existing remote:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/your-repo.git
```

### Problem: "Authentication failed" when pushing
**Causes:**
1. Token is incorrect or expired
2. Token doesn't have `repo` scope
3. Repository URL is wrong

**Solutions:**
- Verify token is copied correctly (starts with `ghp_`)
- Check token has `repo` permission in GitHub settings
- Verify repository URL: `git remote -v`

### Problem: "permission denied" or "repository not found"
**Solutions:**
- Check repository exists on GitHub
- Verify you're the owner of the repository
- Ensure repository is not set to private (unless token has access)

### Problem: App not updating after deploy
**Solutions:**
1. Check deployment logs for errors
2. Verify the app is pulling from the correct branch (`main`)
3. Clear browser cache and hard refresh (Ctrl+Shift+R)
4. Check commit hash in deployment matches your latest commit

---

## 📝 Quick Reference Commands

```bash
# Check git status
git status

# View remote configuration
git remote -v

# View commit history
git log --oneline -5

# View what files are tracked
git ls-tree -r main --name-only

# Push to GitHub (with token)
git push https://TOKEN@github.com/USERNAME/REPO.git main

# View Databricks app info
databricks apps get APP_NAME

# View app logs
databricks apps logs APP_NAME

# List all apps
databricks apps list
```

---

## 📚 Additional Resources

- **GitHub Personal Access Tokens:** https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- **Databricks Apps Documentation:** https://docs.databricks.com/en/dev-tools/apps/index.html
- **Git Basics:** https://git-scm.com/book/en/v2/Getting-Started-Git-Basics

---

## ✅ Checklist

Use this checklist for each deployment:

- [ ] Created new GitHub repository
- [ ] Copied files to fresh workspace directory
- [ ] Initialized git and configured user
- [ ] Made necessary modifications
- [ ] Committed all changes
- [ ] Added GitHub remote
- [ ] Created GitHub Personal Access Token with `repo` scope
- [ ] Pushed to GitHub successfully
- [ ] Verified files appear on GitHub
- [ ] Updated Databricks App configuration
- [ ] Deployed app
- [ ] Verified app is running with changes
- [ ] **REVOKED GitHub token**

---

## 💡 Pro Tips

1. **Never commit tokens or secrets** - Use environment variables or Databricks secrets
2. **Use meaningful commit messages** - Makes it easier to track changes
3. **Test locally first** - If possible, test changes before deploying
4. **Use branches for experimentation** - Keep `main` stable, create feature branches
5. **Document your changes** - Update README.md with modifications
6. **Version your app** - Tag releases in git for easy rollback

---

## 🤝 Contributing

If you improve this guide or find issues:
1. Create an issue or PR in the repository
2. Share your improvements with the team
3. Help others who face similar challenges

---

**Last Updated:** August 2026  
**Version:** 1.0