"""파일 시스템 감시 모듈."""

import os
import time
import logging
from pathlib import Path
from typing import Callable, Dict, List, Set
from dataclasses import dataclass
from enum import Enum
from threading import Thread, Event
from datetime import datetime

logger = logging.getLogger(__name__)


class FileChangeType(Enum):
    """파일 변경 유형."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileChangeEvent:
    """파일 변경 이벤트."""
    path: Path
    change_type: FileChangeType
    timestamp: datetime
    file_type: str  # 'ifc' or 'bcf'


class FileWatcher:
    """파일 시스템 감시기 - IFC 및 BCF 파일 변경 감지."""
    
    def __init__(self, watch_dirs: List[Path], poll_interval: float = 2.0):
        """
        Args:
            watch_dirs: 감시할 디렉토리 목록
            poll_interval: 폴링 간격 (초)
        """
        self.watch_dirs = [Path(d) for d in watch_dirs]
        self.poll_interval = poll_interval
        self.callbacks: List[Callable[[FileChangeEvent], None]] = []
        
        # 파일 상태 추적
        self.file_states: Dict[Path, float] = {}  # path -> mtime
        self._stop_event = Event()
        self._thread: Thread = None
        
        logger.info(f"FileWatcher 초기화: {len(self.watch_dirs)}개 디렉토리 감시")
    
    def register_callback(self, callback: Callable[[FileChangeEvent], None]):
        """변경 감지 시 호출할 콜백 등록."""
        self.callbacks.append(callback)
        logger.info(f"콜백 등록: {callback.__name__}")
    
    def _scan_files(self) -> Dict[Path, float]:
        """현재 파일 상태 스캔."""
        current_files = {}
        
        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                logger.warning(f"감시 디렉토리가 존재하지 않음: {watch_dir}")
                continue
            
            # IFC 파일 스캔
            for ifc_file in watch_dir.glob("**/*.ifc"):
                if ifc_file.is_file():
                    current_files[ifc_file] = ifc_file.stat().st_mtime
            
            # BCF 파일 스캔
            for bcf_file in watch_dir.glob("**/*.bcfzip"):
                if bcf_file.is_file():
                    current_files[bcf_file] = bcf_file.stat().st_mtime
        
        return current_files
    
    def _detect_changes(self, current_files: Dict[Path, float]) -> List[FileChangeEvent]:
        """파일 변경 감지."""
        events = []
        current_paths = set(current_files.keys())
        previous_paths = set(self.file_states.keys())
        
        # 새로 생성된 파일
        for path in current_paths - previous_paths:
            file_type = 'ifc' if path.suffix == '.ifc' else 'bcf'
            events.append(FileChangeEvent(
                path=path,
                change_type=FileChangeType.CREATED,
                timestamp=datetime.now(),
                file_type=file_type
            ))
        
        # 수정된 파일
        for path in current_paths & previous_paths:
            if current_files[path] != self.file_states[path]:
                file_type = 'ifc' if path.suffix == '.ifc' else 'bcf'
                events.append(FileChangeEvent(
                    path=path,
                    change_type=FileChangeType.MODIFIED,
                    timestamp=datetime.now(),
                    file_type=file_type
                ))
        
        # 삭제된 파일
        for path in previous_paths - current_paths:
            file_type = 'ifc' if path.suffix == '.ifc' else 'bcf'
            events.append(FileChangeEvent(
                path=path,
                change_type=FileChangeType.DELETED,
                timestamp=datetime.now(),
                file_type=file_type
            ))
        
        return events
    
    def _watch_loop(self):
        """파일 감시 루프."""
        logger.info("파일 감시 시작")
        
        # 초기 스캔
        self.file_states = self._scan_files()
        logger.info(f"초기 스캔 완료: {len(self.file_states)}개 파일")
        
        while not self._stop_event.is_set():
            try:
                # 현재 파일 상태 스캔
                current_files = self._scan_files()
                
                # 변경 감지
                events = self._detect_changes(current_files)
                
                # 이벤트 처리
                for event in events:
                    logger.info(
                        f"파일 변경 감지: {event.change_type.value} - "
                        f"{event.path.name} ({event.file_type})"
                    )
                    
                    # 콜백 호출
                    for callback in self.callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            logger.error(f"콜백 실행 오류: {e}", exc_info=True)
                
                # 상태 업데이트
                self.file_states = current_files
                
                # 대기
                self._stop_event.wait(self.poll_interval)
                
            except Exception as e:
                logger.error(f"파일 감시 오류: {e}", exc_info=True)
                self._stop_event.wait(self.poll_interval)
    
    def start(self):
        """파일 감시 시작."""
        if self._thread and self._thread.is_alive():
            logger.warning("파일 감시가 이미 실행 중입니다")
            return
        
        self._stop_event.clear()
        self._thread = Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info("파일 감시 스레드 시작")
    
    def stop(self):
        """파일 감시 중지."""
        if not self._thread or not self._thread.is_alive():
            logger.warning("파일 감시가 실행 중이 아닙니다")
            return
        
        logger.info("파일 감시 중지 중...")
        self._stop_event.set()
        self._thread.join(timeout=5.0)
        logger.info("파일 감시 중지 완료")
    
    def is_running(self) -> bool:
        """파일 감시 실행 여부."""
        return self._thread is not None and self._thread.is_alive()

