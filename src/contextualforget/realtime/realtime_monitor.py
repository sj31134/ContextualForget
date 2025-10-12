"""실시간 모니터링 시스템."""

import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .file_watcher import FileWatcher, FileChangeEvent
from .graph_updater import GraphUpdater

logger = logging.getLogger(__name__)


class RealtimeMonitor:
    """실시간 데이터 모니터링 시스템."""
    
    def __init__(
        self,
        watch_dirs: List[Path],
        graph_path: Path,
        processed_dir: Path,
        poll_interval: float = 2.0
    ):
        """
        Args:
            watch_dirs: 감시할 디렉토리 목록
            graph_path: 그래프 파일 경로
            processed_dir: 처리된 데이터 저장 디렉토리
            poll_interval: 폴링 간격 (초)
        """
        self.watch_dirs = [Path(d) for d in watch_dirs]
        self.graph_path = Path(graph_path)
        self.processed_dir = Path(processed_dir)
        self.poll_interval = poll_interval
        
        # 컴포넌트 초기화
        self.file_watcher = FileWatcher(watch_dirs, poll_interval)
        self.graph_updater = GraphUpdater(graph_path, processed_dir)
        
        # 파일 변경 이벤트 콜백 등록
        self.file_watcher.register_callback(self._on_file_changed)
        
        # 통계
        self.stats = {
            'start_time': None,
            'files_processed': 0,
            'ifc_files': 0,
            'bcf_files': 0,
            'errors': 0,
            'last_update': None
        }
        
        logger.info("RealtimeMonitor 초기화 완료")
    
    def _on_file_changed(self, event: FileChangeEvent):
        """파일 변경 이벤트 핸들러."""
        try:
            # 그래프 업데이트
            self.graph_updater.handle_file_change(event)
            
            # 통계 업데이트
            self.stats['files_processed'] += 1
            if event.file_type == 'ifc':
                self.stats['ifc_files'] += 1
            elif event.file_type == 'bcf':
                self.stats['bcf_files'] += 1
            self.stats['last_update'] = datetime.now().isoformat()
            
            logger.info(
                f"파일 처리 완료: {event.path.name} "
                f"(총 {self.stats['files_processed']}개)"
            )
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"파일 변경 처리 오류: {e}", exc_info=True)
    
    def start(self):
        """실시간 모니터링 시작."""
        logger.info("=" * 60)
        logger.info("실시간 모니터링 시작")
        logger.info(f"감시 디렉토리: {[str(d) for d in self.watch_dirs]}")
        logger.info(f"그래프 파일: {self.graph_path}")
        logger.info(f"폴링 간격: {self.poll_interval}초")
        logger.info("=" * 60)
        
        self.stats['start_time'] = datetime.now().isoformat()
        
        # 파일 감시 시작
        self.file_watcher.start()
        
        logger.info("실시간 모니터링이 시작되었습니다.")
        logger.info("파일 변경 시 자동으로 그래프가 업데이트됩니다.")
    
    def stop(self):
        """실시간 모니터링 중지."""
        logger.info("실시간 모니터링 중지 중...")
        
        # 파일 감시 중지
        self.file_watcher.stop()
        
        # 최종 그래프 저장
        self.graph_updater.save_graph()
        
        logger.info("=" * 60)
        logger.info("실시간 모니터링 통계:")
        logger.info(f"  실행 시간: {self.stats['start_time']} ~ {datetime.now().isoformat()}")
        logger.info(f"  처리된 파일: {self.stats['files_processed']}개")
        logger.info(f"    - IFC: {self.stats['ifc_files']}개")
        logger.info(f"    - BCF: {self.stats['bcf_files']}개")
        logger.info(f"  오류: {self.stats['errors']}개")
        logger.info(f"  마지막 업데이트: {self.stats['last_update']}")
        logger.info("=" * 60)
        
        logger.info("실시간 모니터링 중지 완료")
    
    def is_running(self) -> bool:
        """모니터링 실행 여부."""
        return self.file_watcher.is_running()
    
    def get_stats(self) -> dict:
        """통계 정보 반환."""
        return {
            **self.stats,
            'is_running': self.is_running(),
            'current_time': datetime.now().isoformat()
        }
    
    def trigger_full_scan(self):
        """전체 스캔 트리거 (수동)."""
        logger.info("전체 스캔 트리거")
        
        # 현재 파일 상태 강제 업데이트
        if self.file_watcher.is_running():
            logger.info("파일 감시기가 다음 폴링 주기에 변경 사항을 감지합니다.")
        else:
            logger.warning("파일 감시기가 실행 중이 아닙니다. start()를 먼저 호출하세요.")

