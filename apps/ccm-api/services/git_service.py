import git
import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import Config
from models.events import CommitSuggestion, BranchSuggestion

class GitService:
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or Config.DEFAULT_GIT_REPO_PATH
        self.repo = None
        self._initialize_repo()

    def _initialize_repo(self):
        """Initialize git repository"""
        try:
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            print(f"Warning: {self.repo_path} is not a valid git repository")
            self.repo = None

    async def get_current_status(self) -> Dict[str, Any]:
        """Get current git status"""
        if not self.repo:
            return {"error": "No git repository"}

        try:
            return {
                "branch": self.repo.active_branch.name,
                "commit": self.repo.head.commit.hexsha[:8],
                "modified_files": [item.a_path for item in self.repo.index.diff(None)],
                "staged_files": [item.a_path for item in self.repo.index.diff("HEAD")],
                "untracked_files": self.repo.untracked_files,
                "is_dirty": self.repo.is_dirty()
            }
        except Exception as e:
            return {"error": f"Git status error: {str(e)}"}

    async def get_recent_commits(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits"""
        if not self.repo:
            return []

        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=count):
                commits.append({
                    "hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "date": commit.committed_datetime.isoformat(),
                    "files": list(commit.stats.files.keys())
                })
            return commits
        except Exception as e:
            print(f"Error getting recent commits: {e}")
            return []

    async def get_diff(self, cached: bool = False) -> str:
        """Get current diff"""
        if not self.repo:
            return ""

        try:
            if cached:
                # Staged changes
                return self.repo.git.diff("--cached")
            else:
                # Working directory changes
                return self.repo.git.diff()
        except Exception as e:
            print(f"Error getting diff: {e}")
            return ""

    async def create_commit(self, message: str, files: List[str] = None, auto_stage: bool = False) -> Dict[str, Any]:
        """Create a commit"""
        if not self.repo:
            return {"error": "No git repository"}

        try:
            if auto_stage:
                if files:
                    # Stage specific files
                    self.repo.index.add(files)
                else:
                    # Stage all modified files
                    self.repo.git.add(A=True)

            # Check if there are staged changes
            if not self.repo.index.diff("HEAD"):
                return {"error": "No staged changes to commit"}

            # Create commit
            commit = self.repo.index.commit(message)

            return {
                "hash": commit.hexsha[:8],
                "message": message,
                "files": list(commit.stats.files.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Commit failed: {str(e)}"}

    async def create_branch(self, branch_name: str, checkout: bool = True) -> Dict[str, Any]:
        """Create a new branch"""
        if not self.repo:
            return {"error": "No git repository"}

        try:
            # Check if branch already exists
            if branch_name in [ref.name.split('/')[-1] for ref in self.repo.refs]:
                return {"error": f"Branch '{branch_name}' already exists"}

            # Create new branch
            new_branch = self.repo.create_head(branch_name)

            if checkout:
                new_branch.checkout()

            return {
                "branch": branch_name,
                "checked_out": checkout,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Branch creation failed: {str(e)}"}

    async def detect_merge_conflicts(self) -> List[Dict[str, Any]]:
        """Detect merge conflicts"""
        if not self.repo:
            return []

        try:
            conflicts = []

            # Check if we're in a merge state
            if os.path.exists(os.path.join(self.repo.git_dir, "MERGE_HEAD")):
                # Get conflicted files
                status = self.repo.git.status(porcelain=True)
                for line in status.split('\n'):
                    if line.startswith('UU'):  # Both modified (conflict)
                        file_path = line[3:]
                        conflicts.append({
                            "file": file_path,
                            "type": "both_modified",
                            "status": "unmerged"
                        })

            return conflicts
        except Exception as e:
            print(f"Error detecting conflicts: {e}")
            return []

    async def analyze_intent_drift(self, recent_commits: List[Dict[str, Any]], original_intent: str) -> Dict[str, Any]:
        """Analyze if recent commits drift from original intent"""
        if not recent_commits:
            return {"drift_detected": False, "confidence": 0.0}

        # Simple keyword-based analysis (can be enhanced with embeddings)
        intent_keywords = set(original_intent.lower().split())

        drift_scores = []
        for commit in recent_commits[-5:]:  # Check last 5 commits
            commit_words = set(commit["message"].lower().split())

            # Calculate overlap
            overlap = len(intent_keywords.intersection(commit_words))
            total_words = len(intent_keywords.union(commit_words))

            similarity = overlap / total_words if total_words > 0 else 0
            drift_scores.append(1 - similarity)  # Higher score = more drift

        avg_drift = sum(drift_scores) / len(drift_scores)

        return {
            "drift_detected": avg_drift > Config().INTENT_DRIFT_THRESHOLD,
            "confidence": avg_drift,
            "recent_commits": len(recent_commits),
            "analysis": "Keyword-based similarity analysis"
        }

    async def suggest_branch_cleanup(self) -> List[Dict[str, Any]]:
        """Suggest branches that can be cleaned up"""
        if not self.repo:
            return []

        try:
            suggestions = []
            current_branch = self.repo.active_branch.name

            for branch in self.repo.heads:
                if branch.name == current_branch:
                    continue

                # Check if branch is merged
                try:
                    self.repo.git.merge_base("--is-ancestor", branch.commit, "HEAD")
                    is_merged = True
                except git.GitCommandError:
                    is_merged = False

                # Check last commit date
                last_commit_date = branch.commit.committed_datetime
                days_old = (datetime.now(last_commit_date.tzinfo) - last_commit_date).days

                if is_merged or days_old > 30:
                    suggestions.append({
                        "branch": branch.name,
                        "reason": "merged" if is_merged else f"stale ({days_old} days old)",
                        "last_commit": last_commit_date.isoformat(),
                        "safe_to_delete": is_merged
                    })

            return suggestions
        except Exception as e:
            print(f"Error analyzing branches: {e}")
            return []
