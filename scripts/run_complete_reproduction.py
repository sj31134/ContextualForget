#!/usr/bin/env python3
"""
Complete Reproduction Script for ContextualForget RAG System

This script runs the complete reproduction workflow for the ContextualForget RAG system,
including data integration, evaluation, statistical validation, and visualization generation.

Usage:
    python scripts/run_complete_reproduction.py [--phase PHASE] [--skip-validation] [--verbose]

Arguments:
    --phase: Run specific phase (1-4) or 'all' (default: all)
    --skip-validation: Skip validation steps
    --verbose: Enable verbose output
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reproduction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReproductionRunner:
    def __init__(self, skip_validation=False, verbose=False):
        self.skip_validation = skip_validation
        self.verbose = verbose
        self.start_time = datetime.now()
        self.results = {}
        
    def run_command(self, command, description):
        """Run a command and log the results"""
        logger.info(f"🚀 {description}")
        logger.info(f"Command: {command}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ {description} completed successfully ({duration:.2f}s)")
                if self.verbose and result.stdout:
                    logger.info(f"Output: {result.stdout}")
                return True
            else:
                logger.error(f"❌ {description} failed ({duration:.2f}s)")
                logger.error(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {description} failed with exception: {e}")
            return False
    
    def run_phase_1(self):
        """Phase 1: Data Integration and Quality Assessment"""
        logger.info("=" * 60)
        logger.info("PHASE 1: Data Integration and Quality Assessment")
        logger.info("=" * 60)
        
        phase_1_scripts = [
            ("python scripts/restore_original_data.py", "Restore original data from raw files"),
            ("python scripts/build_integrated_dataset.py", "Build integrated dataset"),
            ("python scripts/integrate_real_bcf_data.py", "Integrate real BCF data"),
            ("python scripts/compare_data_quality.py", "Compare data quality"),
            ("python scripts/rebuild_graph_with_real_data.py", "Rebuild graph with real data"),
            ("python scripts/test_real_data_evaluation.py", "Test real data evaluation")
        ]
        
        success_count = 0
        for command, description in phase_1_scripts:
            if self.run_command(command, description):
                success_count += 1
            else:
                logger.warning(f"⚠️ {description} failed, continuing with next step")
        
        self.results['phase_1'] = {
            'success_count': success_count,
            'total_scripts': len(phase_1_scripts),
            'success_rate': success_count / len(phase_1_scripts)
        }
        
        logger.info(f"Phase 1 completed: {success_count}/{len(phase_1_scripts)} scripts successful")
        return success_count == len(phase_1_scripts)
    
    def run_phase_2(self):
        """Phase 2: Gold Standard Expansion"""
        logger.info("=" * 60)
        logger.info("PHASE 2: Gold Standard Expansion")
        logger.info("=" * 60)
        
        phase_2_scripts = [
            ("python scripts/fix_gold_standard_and_graph.py", "Fix Gold Standard and graph"),
            ("python scripts/create_simple_connections.py", "Create simple connections"),
            ("python scripts/generate_diverse_queries.py", "Generate diverse queries"),
            ("python scripts/test_fixed_data_evaluation.py", "Test fixed data evaluation")
        ]
        
        success_count = 0
        for command, description in phase_2_scripts:
            if self.run_command(command, description):
                success_count += 1
            else:
                logger.warning(f"⚠️ {description} failed, continuing with next step")
        
        self.results['phase_2'] = {
            'success_count': success_count,
            'total_scripts': len(phase_2_scripts),
            'success_rate': success_count / len(phase_2_scripts)
        }
        
        logger.info(f"Phase 2 completed: {success_count}/{len(phase_2_scripts)} scripts successful")
        return success_count == len(phase_2_scripts)
    
    def run_phase_3(self):
        """Phase 3: Comprehensive Evaluation"""
        logger.info("=" * 60)
        logger.info("PHASE 3: Comprehensive Evaluation")
        logger.info("=" * 60)
        
        phase_3_scripts = [
            ("python scripts/comprehensive_evaluation_extended.py", "Run extended evaluation"),
            ("python scripts/scalability_benchmark.py", "Run scalability benchmark"),
            ("python scripts/statistical_validation_rq.py", "Perform statistical validation")
        ]
        
        success_count = 0
        for command, description in phase_3_scripts:
            if self.run_command(command, description):
                success_count += 1
            else:
                logger.warning(f"⚠️ {description} failed, continuing with next step")
        
        self.results['phase_3'] = {
            'success_count': success_count,
            'total_scripts': len(phase_3_scripts),
            'success_rate': success_count / len(phase_3_scripts)
        }
        
        logger.info(f"Phase 3 completed: {success_count}/{len(phase_3_scripts)} scripts successful")
        return success_count == len(phase_3_scripts)
    
    def run_phase_4(self):
        """Phase 4: Visualization and Analysis"""
        logger.info("=" * 60)
        logger.info("PHASE 4: Visualization and Analysis")
        logger.info("=" * 60)
        
        phase_4_scripts = [
            ("python scripts/generate_visualizations.py", "Generate visualizations"),
            ("python scripts/create_architecture_diagrams.py", "Create architecture diagrams")
        ]
        
        success_count = 0
        for command, description in phase_4_scripts:
            if self.run_command(command, description):
                success_count += 1
            else:
                logger.warning(f"⚠️ {description} failed, continuing with next step")
        
        self.results['phase_4'] = {
            'success_count': success_count,
            'total_scripts': len(phase_4_scripts),
            'success_rate': success_count / len(phase_4_scripts)
        }
        
        logger.info(f"Phase 4 completed: {success_count}/{len(phase_4_scripts)} scripts successful")
        return success_count == len(phase_4_scripts)
    
    def run_validation(self):
        """Run validation scripts"""
        if self.skip_validation:
            logger.info("⏭️ Skipping validation as requested")
            return True
            
        logger.info("=" * 60)
        logger.info("VALIDATION")
        logger.info("=" * 60)
        
        validation_scripts = [
            ("python scripts/validate_system.py", "Validate system setup"),
            ("python scripts/validate_results.py", "Validate results"),
            ("python scripts/benchmark_performance.py", "Benchmark performance")
        ]
        
        success_count = 0
        for command, description in validation_scripts:
            if self.run_command(command, description):
                success_count += 1
            else:
                logger.warning(f"⚠️ {description} failed")
        
        self.results['validation'] = {
            'success_count': success_count,
            'total_scripts': len(validation_scripts),
            'success_rate': success_count / len(validation_scripts)
        }
        
        logger.info(f"Validation completed: {success_count}/{len(validation_scripts)} scripts successful")
        return success_count == len(validation_scripts)
    
    def generate_summary_report(self):
        """Generate a summary report of the reproduction run"""
        total_duration = datetime.now() - self.start_time
        
        report = f"""
# ContextualForget RAG System - Reproduction Summary Report

**Run Date**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**Total Duration**: {total_duration}
**Skip Validation**: {self.skip_validation}
**Verbose Mode**: {self.verbose}

## Phase Results

"""
        
        for phase, results in self.results.items():
            report += f"""
### {phase.replace('_', ' ').title()}
- **Success Rate**: {results['success_rate']:.1%} ({results['success_count']}/{results['total_scripts']})
- **Status**: {'✅ PASSED' if results['success_rate'] == 1.0 else '⚠️ PARTIAL' if results['success_rate'] > 0.5 else '❌ FAILED'}

"""
        
        # Overall status
        overall_success = all(results['success_rate'] == 1.0 for results in self.results.values())
        report += f"""
## Overall Status

**Overall Success**: {'✅ PASSED' if overall_success else '⚠️ PARTIAL/FAILED'}

## Generated Files

Check the following directories for generated results:
- `results/evaluation_extended/` - Comprehensive evaluation results
- `results/scalability_benchmark/` - Scalability analysis
- `results/statistical_validation/` - Statistical validation results
- `results/visualizations/` - Performance visualizations
- `docs/diagrams/` - System architecture diagrams

## Next Steps

1. Review the generated results and visualizations
2. Check the reproduction.log file for detailed execution logs
3. Run individual validation scripts if needed
4. Compare results with expected performance metrics

## Troubleshooting

If any phase failed:
1. Check the reproduction.log file for error details
2. Verify data availability in the `data/` directory
3. Ensure all dependencies are installed
4. Run individual scripts to isolate issues

---
*Generated by run_complete_reproduction.py*
"""
        
        # Save report
        report_file = Path("reproduction_summary.md")
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Summary report saved to: {report_file}")
        print(report)
    
    def run(self, phase='all'):
        """Run the complete reproduction workflow"""
        logger.info("🚀 Starting ContextualForget RAG System Reproduction")
        logger.info(f"Phase: {phase}, Skip Validation: {self.skip_validation}, Verbose: {self.verbose}")
        
        phases_to_run = []
        
        if phase == 'all':
            phases_to_run = ['phase_1', 'phase_2', 'phase_3', 'phase_4']
        elif phase == '1':
            phases_to_run = ['phase_1']
        elif phase == '2':
            phases_to_run = ['phase_2']
        elif phase == '3':
            phases_to_run = ['phase_3']
        elif phase == '4':
            phases_to_run = ['phase_4']
        else:
            logger.error(f"Invalid phase: {phase}. Use 'all', '1', '2', '3', or '4'")
            return False
        
        # Run phases
        for phase_name in phases_to_run:
            if phase_name == 'phase_1':
                self.run_phase_1()
            elif phase_name == 'phase_2':
                self.run_phase_2()
            elif phase_name == 'phase_3':
                self.run_phase_3()
            elif phase_name == 'phase_4':
                self.run_phase_4()
        
        # Run validation
        self.run_validation()
        
        # Generate summary report
        self.generate_summary_report()
        
        logger.info("🎉 Reproduction workflow completed!")
        return True

def main():
    parser = argparse.ArgumentParser(description='Run complete ContextualForget RAG system reproduction')
    parser.add_argument('--phase', default='all', choices=['all', '1', '2', '3', '4'],
                       help='Phase to run (default: all)')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip validation steps')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    runner = ReproductionRunner(
        skip_validation=args.skip_validation,
        verbose=args.verbose
    )
    
    success = runner.run(phase=args.phase)
    
    if success:
        logger.info("✅ Reproduction completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Reproduction completed with errors!")
        sys.exit(1)

if __name__ == "__main__":
    main()
