#!/usr/bin/env python3
import subprocess
import os
import sys
import argparse

def check_git_status(directory):
    """Check if directory is a git repository and its status"""
    if not os.path.exists(os.path.join(directory, '.git')):
        return 'not_initialized'
    
    try:
        # Check if repository is clean
        result = subprocess.run(['git', 'status', '--porcelain'],
                              cwd=directory,
                              capture_output=True,
                              text=True)
        
        if result.returncode != 0:
            return 'error'
        
        # If output is empty, repository is clean
        if not result.stdout.strip():
            # Check if we're up to date with remote
            result = subprocess.run(['git', 'status', '-uno'],
                                 cwd=directory,
                                 capture_output=True,
                                 text=True)
            if 'Your branch is up to date' in result.stdout:
                return 'clean'
            return 'needs_push'
        
        return 'needs_commit'
    except subprocess.SubprocessError:
        return 'error'

def get_current_branch(directory):
    """Get the current git branch name"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'],
                              cwd=directory,
                              capture_output=True,
                              text=True)
        return result.stdout.strip()
    except subprocess.SubprocessError:
        return None

def push_changes(directory, branch=None):
    """Initialize repository if needed and push changes"""
    status = check_git_status(directory)
    
    print(f"\nProcessing directory: {directory}")
    
    if status == 'error':
        print("Error: Unable to check git status")
        return False
    
    if status == 'not_initialized':
        try:
            print("Initializing git repository...")
            subprocess.run(['git', 'init'], cwd=directory, check=True)
        except subprocess.SubprocessError:
            print("Error: Failed to initialize git repository")
            return False
    
    if status == 'clean':
        print("Repository is clean and up to date")
        return True
    
    current_branch = get_current_branch(directory)
    if not current_branch:
        print("Error: Unable to determine current branch")
        return False
    
    if status in ['needs_commit', 'needs_push']:
        try:
            # Add changes
            print("Adding changes...")
            subprocess.run(['git', 'add', '.'], cwd=directory, check=True)
            
            # Commit changes
            print("Committing changes...")
            subprocess.run(['git', 'commit', '-m', 'Automated commit'],
                         cwd=directory,
                         check=True)
            
            # Handle branch selection
            target_branch = branch or current_branch
            if not branch:
                response = input(f"Push to current branch '{current_branch}'? (y/n): ")
                if response.lower() != 'y':
                    target_branch = input("Enter target branch name: ")
            
            if target_branch != current_branch:
                print(f"Switching to branch {target_branch}...")
                subprocess.run(['git', 'checkout', '-B', target_branch],
                             cwd=directory,
                             check=True)
            
            # Push changes
            print(f"Pushing to branch '{target_branch}'...")
            result = subprocess.run(['git', 'push', 'origin', target_branch],
                                 cwd=directory,
                                 capture_output=True,
                                 text=True)
            
            if result.returncode != 0:
                if 'Permission denied' in result.stderr:
                    print("Error: Permission denied. Please check your access rights and try again.")
                else:
                    print(f"Error pushing changes: {result.stderr}")
                return False
            
            print("Successfully pushed changes")
            return True
            
        except subprocess.SubprocessError as e:
            print(f"Error during git operations: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Automate git operations for multiple directories')
    parser.add_argument('--dirs', nargs='+', help='Directories to process')
    parser.add_argument('--file', help='File containing list of directories')
    parser.add_argument('--branch', help='Target branch for push')
    args = parser.parse_args()
    
    directories = []
    
    if args.dirs:
        directories.extend(args.dirs)
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                directories.extend(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            print(f"Error: File {args.file} not found")
            sys.exit(1)
    
    if not directories:
        print("Error: No directories specified")
        parser.print_help()
        sys.exit(1)
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"Warning: Directory {directory} does not exist, skipping")
            continue
            
        push_changes(directory, args.branch)



"""
Usage:
python git_automation.py --dirs /path/to/dir1 /path/to/dir2 /path/to/dir3
python git_automation.py --file directories.txt
python git_automation.py --dirs /path/to/dir1 --branch main
"""
if __name__ == '__main__':
    main()
