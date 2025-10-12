#!/usr/bin/env python3
"""실시간 모니터링 데모 스크립트 - 새 파일을 주기적으로 생성하여 실시간 업데이트 시연."""

import time
import random
from pathlib import Path
from datetime import datetime


def generate_demo_ifc(filename: str, building_name: str) -> str:
    """간단한 데모 IFC 파일 생성."""
    guid = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$', k=22))
    
    return f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('{filename}','{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}',('Demo User'),('ContextualForget'),'Demo','Demo-1.0','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;

DATA;
#1=IFCPROJECT('{guid}',$,'{building_name}',$,$,$,$,(#2),#3);
#2=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#4,$);
#3=IFCUNITASSIGNMENT((#5));
#4=IFCAXIS2PLACEMENT3D(#6,$,$);
#5=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#6=IFCCARTESIANPOINT((0.,0.,0.));
#7=IFCBUILDING('{guid}',$,'{building_name}',$,$,#8,$,$,.ELEMENT.,$,$,$);
#8=IFCLOCALPLACEMENT($,#9);
#9=IFCAXIS2PLACEMENT3D(#6,$,$);
#10=IFCWALL('{guid}',$,'Demo Wall',$,$,#8,$,$);
#11=IFCSLAB('{guid}',$,'Demo Slab',$,$,#8,$,$,.FLOOR.);
ENDSEC;
END-ISO-10303-21;"""


def main():
    """메인 함수."""
    print("🎬 실시간 모니터링 데모")
    print("=" * 60)
    print("이 스크립트는 새로운 IFC 파일을 주기적으로 생성하여")
    print("실시간 모니터링 기능을 시연합니다.")
    print("")
    print("사용법:")
    print("1. 터미널 1: python scripts/demo_realtime.py")
    print("2. 터미널 2: ctxf watch -w data/demo -i 2.0")
    print("=" * 60)
    
    # 데모 디렉토리 생성
    base_dir = Path(__file__).parent.parent
    demo_dir = base_dir / "data" / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 데모 디렉토리: {demo_dir}")
    print("\n⏱️  5초마다 새로운 IFC 파일을 생성합니다...")
    print("중지하려면 Ctrl+C를 누르세요.\n")
    
    building_types = ["Office", "Residential", "Hospital", "School", "Factory"]
    counter = 1
    
    try:
        while True:
            building_type = random.choice(building_types)
            building_name = f"{building_type} Building {counter}"
            filename = f"demo_{building_type.lower()}_{counter}.ifc"
            filepath = demo_dir / filename
            
            # IFC 파일 생성
            ifc_content = generate_demo_ifc(filename, building_name)
            with open(filepath, 'w') as f:
                f.write(ifc_content)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ✅ 생성: {filename} ({building_name})")
            
            counter += 1
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  데모 중지")
        print(f"\n총 {counter - 1}개의 파일을 생성했습니다.")
        print("\n💡 데모 파일을 정리하려면:")
        print(f"   rm -rf {demo_dir}")


if __name__ == "__main__":
    main()

