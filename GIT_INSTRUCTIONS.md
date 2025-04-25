# Git Instructions for Cluedo Game Project

This document provides instructions on how to use Git for version control of your Cluedo game project.

## Current Status

You have successfully:
1. Initialized a Git repository
2. Created a `.gitignore` file to exclude unnecessary files
3. Made an initial commit with all your project files

## Connecting to a Remote Repository

To back up your project to a remote repository (like GitHub, GitLab, etc.):

### GitHub

1. Create a new repository on GitHub:
   - Go to https://github.com/
   - Sign in to your account
   - Click on the "+" icon in the top right corner and select "New repository"
   - Name your repository (e.g., "cluedo-game")
   - Choose whether to make it public or private
   - Do NOT initialize with README, .gitignore, or license (since you already have these locally)
   - Click "Create repository"

2. Connect your local repository to the GitHub repository:
   ```
   git remote add origin https://github.com/yourusername/cluedo-game.git
   ```

3. Push your code to GitHub:
   ```
   git push -u origin master
   ```

### GitLab

1. Create a new project on GitLab:
   - Go to https://gitlab.com/
   - Sign in to your account
   - Click on "New project"
   - Name your project (e.g., "cluedo-game")
   - Choose whether to make it public or private
   - Do NOT initialize with README (since you already have one locally)
   - Click "Create project"

2. Connect your local repository to the GitLab project:
   ```
   git remote add origin https://gitlab.com/yourusername/cluedo-game.git
   ```

3. Push your code to GitLab:
   ```
   git push -u origin master
   ```

## Basic Git Commands for Future Use

### Checking Status

To see which files have been modified:
```
git status
```

### Viewing Changes

To see what changes you've made:
```
git diff
```

### Staging Changes

To stage specific files for commit:
```
git add filename.py
```

To stage all changes:
```
git add .
```

### Committing Changes

To commit staged changes:
```
git commit -m "Description of changes"
```

### Pushing Changes

To push your commits to the remote repository:
```
git push
```

### Pulling Changes

To pull changes from the remote repository:
```
git pull
```

### Viewing Commit History

To see the commit history:
```
git log
```

For a more concise view:
```
git log --oneline
```

### Creating and Switching Branches

To create a new branch:
```
git branch new-feature
```

To switch to a branch:
```
git checkout new-feature
```

To create and switch to a new branch in one command:
```
git checkout -b new-feature
```

### Merging Branches

To merge changes from another branch into your current branch:
```
git merge branch-name
```

## Best Practices

1. **Commit Often**: Make small, focused commits that address a single issue or feature.
2. **Write Good Commit Messages**: Be clear and descriptive about what changes you made.
3. **Pull Before Push**: Always pull the latest changes before pushing to avoid conflicts.
4. **Use Branches**: Create separate branches for new features or bug fixes.
5. **Review Changes Before Committing**: Use `git status` and `git diff` to review your changes before committing.

## Backing Up Your Project

With Git, you have multiple ways to back up your project:

1. **Regular Pushes**: Push your changes to the remote repository regularly.
2. **Multiple Remotes**: You can add multiple remote repositories for additional backup.
3. **Local Backups**: The `.git` directory contains the entire history of your project, so backing up your project directory also backs up your Git history.

## Getting Help

For more information on Git commands:
```
git help
```

Or for help with a specific command:
```
git help command
```