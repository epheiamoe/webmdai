#!/usr/bin/env python3
"""
Git自动管理模块
"""

from pathlib import Path
from typing import Optional, List

from git import Repo, InvalidGitRepositoryError
from git.exc import GitCommandError


class GitHandler:
    """Git自动管理处理器"""
    
    def __init__(self, directory: Path, enabled: bool = True):
        """
        初始化Git处理器
        
        Args:
            directory: 工作目录
            enabled: 是否启用Git管理
        """
        self.directory = Path(directory).resolve()
        self.enabled = enabled
        self.repo: Optional[Repo] = None
        
        if enabled:
            self._init_repo()
    
    def _init_repo(self):
        """初始化或打开Git仓库"""
        try:
            self.repo = Repo(self.directory)
        except InvalidGitRepositoryError:
            # 目录不是Git仓库，尝试初始化
            try:
                self.repo = Repo.init(self.directory)
                print(f"已在 {self.directory} 初始化Git仓库")
            except Exception as e:
                print(f"警告: 无法初始化Git仓库: {e}")
                self.enabled = False
    
    def is_git_repo(self) -> bool:
        """检查当前目录是否为Git仓库"""
        return self.repo is not None
    
    def has_changes(self) -> bool:
        """检查是否有未提交的更改"""
        if not self.repo:
            return False
        
        return self.repo.is_dirty() or len(self.repo.untracked_files) > 0
    
    def get_changed_files(self) -> List[str]:
        """获取已更改的文件列表"""
        if not self.repo:
            return []
        
        changed = []
        
        # 获取修改的文件
        for item in self.repo.index.diff(None):
            changed.append(item.a_path)
        
        # 获取未跟踪的文件
        changed.extend(self.repo.untracked_files)
        
        return changed
    
    def commit_changes(
        self,
        message: str,
        add_all: bool = True
    ) -> bool:
        """
        提交更改
        
        Args:
            message: 提交信息
            add_all: 是否添加所有更改
            
        Returns:
            是否成功
        """
        if not self.repo or not self.enabled:
            return False
        
        try:
            if add_all:
                # 添加所有更改
                self.repo.git.add(A=True)
            
            # 检查是否有要提交的更改
            if not self.has_changes():
                return True  # 没有更改也算成功
            
            # 提交
            self.repo.index.commit(message)
            return True
            
        except GitCommandError as e:
            print(f"Git提交失败: {e}")
            return False
        except Exception as e:
            print(f"Git操作错误: {e}")
            return False
    
    def create_backup_commit(
        self,
        operation_type: str,
        find: str,
        replace: str = ""
    ) -> bool:
        """
        创建备份提交
        
        Args:
            operation_type: 操作类型
            find: 查找内容
            replace: 替换内容
            
        Returns:
            是否成功
        """
        if not self.enabled:
            return True
        
        # 截断内容以适应提交信息
        find_short = find[:30] + "..." if len(find) > 30 else find
        replace_short = replace[:30] + "..." if len(replace) > 30 else replace
        
        if replace:
            message = f"webmdai: [{operation_type}] {find_short} -> {replace_short}"
        else:
            message = f"webmdai: [{operation_type}] 删除 {find_short}"
        
        return self.commit_changes(message)
    
    def rollback_last_commit(self, hard: bool = False) -> bool:
        """
        回滚最后一次提交
        
        Args:
            hard: 是否强制回滚（会丢失更改）
            
        Returns:
            是否成功
        """
        if not self.repo or not self.enabled:
            return False
        
        try:
            if hard:
                self.repo.git.reset('--hard', 'HEAD~1')
            else:
                self.repo.git.reset('--soft', 'HEAD~1')
            return True
        except GitCommandError as e:
            print(f"回滚失败: {e}")
            return False
    
    def get_last_commit_message(self) -> Optional[str]:
        """获取最后一次提交信息"""
        if not self.repo:
            return None
        
        try:
            return self.repo.head.commit.message
        except Exception:
            return None
    
    def is_webmdai_commit(self) -> bool:
        """检查最后一次提交是否由webmdai创建"""
        message = self.get_last_commit_message()
        return message is not None and message.startswith("webmdai:")
    
    def get_status_summary(self) -> str:
        """获取Git状态摘要"""
        if not self.repo:
            return "Git: 未初始化"
        
        try:
            branch = self.repo.active_branch.name
            dirty = "有未提交更改" if self.has_changes() else "干净"
            return f"Git: 分支 {branch}, {dirty}"
        except Exception as e:
            return f"Git: 状态未知 ({e})"
    
    def stash_changes(self, message: Optional[str] = None) -> bool:
        """
        暂存更改
        
        Args:
            message: 暂存信息
            
        Returns:
            是否成功
        """
        if not self.repo or not self.enabled:
            return False
        
        try:
            if message:
                self.repo.git.stash('save', message)
            else:
                self.repo.git.stash()
            return True
        except GitCommandError as e:
            print(f"暂存失败: {e}")
            return False
    
    def unstash_changes(self) -> bool:
        """
        恢复暂存的更改
        
        Returns:
            是否成功
        """
        if not self.repo or not self.enabled:
            return False
        
        try:
            self.repo.git.stash('pop')
            return True
        except GitCommandError as e:
            print(f"恢复暂存失败: {e}")
            return False
    
    def get_commit_history(self, max_count: int = 10) -> List[dict]:
        """
        获取提交历史
        
        Args:
            max_count: 最大数量
            
        Returns:
            提交信息列表
        """
        if not self.repo:
            return []
        
        history = []
        for commit in self.repo.iter_commits(max_count=max_count):
            history.append({
                'hash': commit.hexsha[:7],
                'message': commit.message.strip(),
                'author': str(commit.author),
                'date': commit.committed_datetime,
            })
        
        return history
