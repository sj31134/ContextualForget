"""
Analytics module for ContextualForget

이 모듈은 그래프 분석, 통계, 인사이트 생성을 담당합니다.
"""

import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns

from ..core.logging import get_logger

logger = get_logger("contextualforget.analytics")


class GraphAnalytics:
    """그래프 분석 및 통계 생성 클래스"""
    
    def __init__(self, graph_path: str):
        """그래프 분석기 초기화"""
        self.graph_path = Path(graph_path)
        self.graph = self._load_graph()
        self.analytics_data = {}
    
    def _load_graph(self) -> nx.DiGraph:
        """그래프 로드"""
        if not self.graph_path.exists():
            raise FileNotFoundError(f"그래프 파일을 찾을 수 없습니다: {self.graph_path}")
        
        with self.graph_path.open('rb') as f:
            graph = pickle.load(f)
        
        logger.info(f"그래프 로드 완료: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 엣지")
        return graph
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """기본 통계 정보 생성"""
        stats = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "ifc_nodes": 0,
            "bcf_nodes": 0,
            "summary_nodes": 0,
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph),
            "number_of_components": nx.number_weakly_connected_components(self.graph)
        }
        
        # 노드 타입별 통계
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            if node_type == 'ifc':
                stats["ifc_nodes"] += 1
            elif node_type == 'bcf':
                stats["bcf_nodes"] += 1
            elif node_type == 'summary':
                stats["summary_nodes"] += 1
        
        # 연결성 통계
        if stats["ifc_nodes"] > 0 and stats["bcf_nodes"] > 0:
            stats["avg_connections_per_ifc"] = stats["total_edges"] / stats["ifc_nodes"]
            stats["avg_connections_per_bcf"] = stats["total_edges"] / stats["bcf_nodes"]
        
        self.analytics_data["basic_stats"] = stats
        return stats
    
    def get_temporal_analysis(self) -> Dict[str, Any]:
        """시간적 분석 수행"""
        temporal_data = {
            "creation_timeline": [],
            "activity_by_month": {},
            "recent_activity": {},
            "oldest_event": None,
            "newest_event": None
        }
        
        creation_dates = []
        
        for node, data in self.graph.nodes(data=True):
            created_at = data.get('created_at')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        date = created_at
                    
                    creation_dates.append(date)
                    temporal_data["creation_timeline"].append({
                        "node_id": node,
                        "type": data.get('type', 'unknown'),
                        "created_at": date.isoformat()
                    })
                    
                    # 월별 활동 통계
                    month_key = date.strftime("%Y-%m")
                    if month_key not in temporal_data["activity_by_month"]:
                        temporal_data["activity_by_month"][month_key] = {"ifc": 0, "bcf": 0}
                    temporal_data["activity_by_month"][month_key][data.get('type', 'unknown')] += 1
                    
                except Exception as e:
                    logger.warning(f"날짜 파싱 오류: {created_at} - {e}")
        
        if creation_dates:
            temporal_data["oldest_event"] = min(creation_dates).isoformat()
            temporal_data["newest_event"] = max(creation_dates).isoformat()
            
            # 최근 활동 (지난 30일)
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_events = [d for d in creation_dates if d >= cutoff_date]
            temporal_data["recent_activity"] = {
                "events_last_30_days": len(recent_events),
                "avg_events_per_day": len(recent_events) / 30
            }
        
        self.analytics_data["temporal_analysis"] = temporal_data
        return temporal_data
    
    def get_connectivity_analysis(self) -> Dict[str, Any]:
        """연결성 분석 수행"""
        connectivity_data = {
            "degree_centrality": {},
            "betweenness_centrality": {},
            "clustering_coefficient": nx.average_clustering(self.graph.to_undirected()),
            "most_connected_nodes": [],
            "isolated_nodes": [],
            "bridge_nodes": []
        }
        
        # 중심성 계산
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        
        connectivity_data["degree_centrality"] = degree_centrality
        connectivity_data["betweenness_centrality"] = betweenness_centrality
        
        # 가장 연결된 노드들
        sorted_by_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
        connectivity_data["most_connected_nodes"] = [
            {"node": node, "degree_centrality": centrality}
            for node, centrality in sorted_by_degree[:10]
        ]
        
        # 고립된 노드들
        isolated = [node for node, degree in self.graph.degree() if degree == 0]
        connectivity_data["isolated_nodes"] = isolated
        
        # 브릿지 노드들 (높은 betweenness centrality)
        sorted_by_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)
        connectivity_data["bridge_nodes"] = [
            {"node": node, "betweenness_centrality": centrality}
            for node, centrality in sorted_by_betweenness[:10]
        ]
        
        self.analytics_data["connectivity_analysis"] = connectivity_data
        return connectivity_data
    
    def get_content_analysis(self) -> Dict[str, Any]:
        """콘텐츠 분석 수행"""
        content_data = {
            "entity_types": {},
            "issue_categories": {},
            "common_keywords": {},
            "text_length_stats": {},
            "language_detection": {}
        }
        
        entity_types = {}
        issue_categories = {}
        all_text = []
        text_lengths = []
        
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            
            # IFC 엔티티 타입 분석
            if node_type == 'ifc':
                entity_type = data.get('ifc_type', 'unknown')
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            # BCF 이슈 카테고리 분석
            elif node_type == 'bcf':
                category = data.get('category', 'unknown')
                issue_categories[category] = issue_categories.get(category, 0) + 1
                
                # 텍스트 분석
                title = data.get('title', '')
                description = data.get('description', '')
                text = f"{title} {description}".strip()
                
                if text:
                    all_text.append(text)
                    text_lengths.append(len(text))
        
        content_data["entity_types"] = entity_types
        content_data["issue_categories"] = issue_categories
        
        if text_lengths:
            content_data["text_length_stats"] = {
                "min_length": min(text_lengths),
                "max_length": max(text_lengths),
                "avg_length": np.mean(text_lengths),
                "median_length": np.median(text_lengths)
            }
        
        # 키워드 분석 (간단한 구현)
        if all_text:
            all_words = []
            for text in all_text:
                words = text.lower().split()
                all_words.extend(words)
            
            word_freq = {}
            for word in all_words:
                if len(word) > 3:  # 3글자 이상만
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 상위 키워드
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            content_data["common_keywords"] = dict(sorted_words[:20])
        
        self.analytics_data["content_analysis"] = content_data
        return content_data
    
    def generate_insights(self) -> List[Dict[str, Any]]:
        """인사이트 생성"""
        insights = []
        
        # 기본 통계 기반 인사이트
        if "basic_stats" in self.analytics_data:
            stats = self.analytics_data["basic_stats"]
            
            if stats["ifc_nodes"] > 0 and stats["bcf_nodes"] > 0:
                ratio = stats["bcf_nodes"] / stats["ifc_nodes"]
                if ratio > 0.5:
                    insights.append({
                        "type": "high_issue_ratio",
                        "severity": "warning",
                        "message": f"BCF 이슈 대비 IFC 요소 비율이 높습니다 ({ratio:.2f}). 프로젝트에 많은 이슈가 있는 것으로 보입니다.",
                        "recommendation": "이슈 해결 우선순위를 재검토하세요."
                    })
                elif ratio < 0.1:
                    insights.append({
                        "type": "low_issue_ratio",
                        "severity": "info",
                        "message": f"BCF 이슈 대비 IFC 요소 비율이 낮습니다 ({ratio:.2f}). 프로젝트가 안정적인 상태입니다.",
                        "recommendation": "현재 상태를 유지하세요."
                    })
        
        # 연결성 기반 인사이트
        if "connectivity_analysis" in self.analytics_data:
            conn = self.analytics_data["connectivity_analysis"]
            
            if len(conn["isolated_nodes"]) > 0:
                insights.append({
                    "type": "isolated_nodes",
                    "severity": "warning",
                    "message": f"{len(conn['isolated_nodes'])}개의 고립된 노드가 있습니다.",
                    "recommendation": "이 노드들이 실제로 필요한지 검토하세요."
                })
        
        # 시간적 분석 기반 인사이트
        if "temporal_analysis" in self.analytics_data:
            temporal = self.analytics_data["temporal_analysis"]
            
            if "recent_activity" in temporal:
                recent = temporal["recent_activity"]
                if recent.get("events_last_30_days", 0) == 0:
                    insights.append({
                        "type": "no_recent_activity",
                        "severity": "info",
                        "message": "최근 30일간 새로운 활동이 없습니다.",
                        "recommendation": "프로젝트 상태를 확인하세요."
                    })
        
        return insights
    
    def create_analytics_report(self, output_path: str) -> Dict[str, Any]:
        """종합 분석 보고서 생성"""
        logger.info("분석 보고서 생성 시작...")
        
        # 모든 분석 수행
        basic_stats = self.get_basic_statistics()
        temporal_analysis = self.get_temporal_analysis()
        connectivity_analysis = self.get_connectivity_analysis()
        content_analysis = self.get_content_analysis()
        insights = self.generate_insights()
        
        # 보고서 구성
        report = {
            "generated_at": datetime.now().isoformat(),
            "graph_path": str(self.graph_path),
            "basic_statistics": basic_stats,
            "temporal_analysis": temporal_analysis,
            "connectivity_analysis": connectivity_analysis,
            "content_analysis": content_analysis,
            "insights": insights,
            "summary": {
                "total_analysis_time": datetime.now().isoformat(),
                "insights_count": len(insights),
                "critical_insights": len([i for i in insights if i.get("severity") == "critical"]),
                "warning_insights": len([i for i in insights if i.get("severity") == "warning"])
            }
        }
        
        # 보고서 저장
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"분석 보고서 저장 완료: {output_path}")
        return report
    
    def create_visualizations(self, output_dir: str):
        """시각화 생성"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 기본 통계 차트
        if "basic_stats" in self.analytics_data:
            self._create_basic_stats_chart(output_dir)
        
        # 시간적 분석 차트
        if "temporal_analysis" in self.analytics_data:
            self._create_temporal_charts(output_dir)
        
        # 연결성 분석 차트
        if "connectivity_analysis" in self.analytics_data:
            self._create_connectivity_charts(output_dir)
        
        # 콘텐츠 분석 차트
        if "content_analysis" in self.analytics_data:
            self._create_content_charts(output_dir)
    
    def _create_basic_stats_chart(self, output_dir: Path):
        """기본 통계 차트 생성"""
        stats = self.analytics_data["basic_stats"]
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Basic Statistics', fontsize=16)
        
        # 노드 타입별 분포
        node_types = ['IFC', 'BCF', 'Summary']
        node_counts = [stats.get('ifc_nodes', 0), stats.get('bcf_nodes', 0), stats.get('summary_nodes', 0)]
        
        axes[0, 0].pie(node_counts, labels=node_types, autopct='%1.1f%%')
        axes[0, 0].set_title('Node Type Distribution')
        
        # 연결성 지표
        connectivity_metrics = ['Density', 'Connected', 'Components']
        connectivity_values = [
            stats.get('density', 0),
            1 if stats.get('is_connected', False) else 0,
            stats.get('number_of_components', 0)
        ]
        
        axes[0, 1].bar(connectivity_metrics, connectivity_values)
        axes[0, 1].set_title('Connectivity Metrics')
        axes[0, 1].set_ylabel('Value')
        
        # 평균 연결 수
        if stats.get('avg_connections_per_ifc', 0) > 0:
            avg_connections = [stats.get('avg_connections_per_ifc', 0), stats.get('avg_connections_per_bcf', 0)]
            connection_types = ['IFC', 'BCF']
            axes[1, 0].bar(connection_types, avg_connections)
            axes[1, 0].set_title('Average Connections per Node Type')
            axes[1, 0].set_ylabel('Connections')
        
        # 전체 통계 요약
        axes[1, 1].text(0.1, 0.8, f"Total Nodes: {stats.get('total_nodes', 0)}", fontsize=12)
        axes[1, 1].text(0.1, 0.6, f"Total Edges: {stats.get('total_edges', 0)}", fontsize=12)
        axes[1, 1].text(0.1, 0.4, f"Density: {stats.get('density', 0):.3f}", fontsize=12)
        axes[1, 1].text(0.1, 0.2, f"Components: {stats.get('number_of_components', 0)}", fontsize=12)
        axes[1, 1].set_title('Summary')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'basic_statistics.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_temporal_charts(self, output_dir: Path):
        """시간적 분석 차트 생성"""
        temporal = self.analytics_data["temporal_analysis"]
        
        if not temporal.get("activity_by_month"):
            return
        
        # 월별 활동 차트
        months = list(temporal["activity_by_month"].keys())
        ifc_counts = [temporal["activity_by_month"][m].get("ifc", 0) for m in months]
        bcf_counts = [temporal["activity_by_month"][m].get("bcf", 0) for m in months]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        x = range(len(months))
        
        ax.bar([i - 0.2 for i in x], ifc_counts, 0.4, label='IFC', alpha=0.8)
        ax.bar([i + 0.2 for i in x], bcf_counts, 0.4, label='BCF', alpha=0.8)
        
        ax.set_xlabel('Month')
        ax.set_ylabel('Number of Events')
        ax.set_title('Activity by Month')
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_dir / 'temporal_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_connectivity_charts(self, output_dir: Path):
        """연결성 분석 차트 생성"""
        conn = self.analytics_data["connectivity_analysis"]
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # 가장 연결된 노드들
        if conn.get("most_connected_nodes"):
            nodes = [item["node"][1][:8] + "..." for item in conn["most_connected_nodes"][:10]]
            centralities = [item["degree_centrality"] for item in conn["most_connected_nodes"][:10]]
            
            axes[0].barh(nodes, centralities)
            axes[0].set_title('Most Connected Nodes (Degree Centrality)')
            axes[0].set_xlabel('Degree Centrality')
        
        # 브릿지 노드들
        if conn.get("bridge_nodes"):
            bridge_nodes = [item["node"][1][:8] + "..." for item in conn["bridge_nodes"][:10]]
            betweenness = [item["betweenness_centrality"] for item in conn["bridge_nodes"][:10]]
            
            axes[1].barh(bridge_nodes, betweenness)
            axes[1].set_title('Bridge Nodes (Betweenness Centrality)')
            axes[1].set_xlabel('Betweenness Centrality')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'connectivity_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_content_charts(self, output_dir: Path):
        """콘텐츠 분석 차트 생성"""
        content = self.analytics_data["content_analysis"]
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 엔티티 타입 분포
        if content.get("entity_types"):
            entity_types = list(content["entity_types"].keys())[:10]
            entity_counts = [content["entity_types"][et] for et in entity_types]
            
            axes[0, 0].pie(entity_counts, labels=entity_types, autopct='%1.1f%%')
            axes[0, 0].set_title('IFC Entity Type Distribution')
        
        # 이슈 카테고리 분포
        if content.get("issue_categories"):
            categories = list(content["issue_categories"].keys())
            category_counts = list(content["issue_categories"].values())
            
            axes[0, 1].bar(categories, category_counts)
            axes[0, 1].set_title('BCF Issue Categories')
            axes[0, 1].set_ylabel('Count')
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 상위 키워드
        if content.get("common_keywords"):
            keywords = list(content["common_keywords"].keys())[:10]
            keyword_counts = list(content["common_keywords"].values())
            
            axes[1, 0].barh(keywords, keyword_counts)
            axes[1, 0].set_title('Top Keywords')
            axes[1, 0].set_xlabel('Frequency')
        
        # 텍스트 길이 분포
        if content.get("text_length_stats"):
            stats = content["text_length_stats"]
            axes[1, 1].text(0.1, 0.8, f"Min Length: {stats.get('min_length', 0)}", fontsize=12)
            axes[1, 1].text(0.1, 0.6, f"Max Length: {stats.get('max_length', 0)}", fontsize=12)
            axes[1, 1].text(0.1, 0.4, f"Avg Length: {stats.get('avg_length', 0):.1f}", fontsize=12)
            axes[1, 1].text(0.1, 0.2, f"Median Length: {stats.get('median_length', 0):.1f}", fontsize=12)
            axes[1, 1].set_title('Text Length Statistics')
            axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'content_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()


def create_analytics_report(graph_path: str, output_dir: str = "analytics"):
    """분석 보고서 생성 함수"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 분석기 초기화
    analytics = GraphAnalytics(graph_path)
    
    # 보고서 생성
    report = analytics.create_analytics_report(output_dir / "analytics_report.json")
    
    # 시각화 생성
    analytics.create_visualizations(output_dir)
    
    print(f"✅ 분석 보고서 생성 완료: {output_dir}")
    print(f"📊 보고서: {output_dir / 'analytics_report.json'}")
    print(f"📈 시각화: {output_dir / '*.png'}")
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ContextualForget Analytics")
    parser.add_argument("--graph", required=True, help="Graph file path")
    parser.add_argument("--output", default="analytics", help="Output directory")
    
    args = parser.parse_args()
    
    create_analytics_report(args.graph, args.output)
