# 학술 BIM 데이터셋 리서치 보고서

**작성일**: 2025년 10월 15일
**목적**: SLABIM, DURAARK, Schependomlaan 데이터셋 적합성 분석

## 1. SLABIM Dataset (HKUST)

**기관**: Hong Kong University of Science and Technology (HKUST)
**설명**: SLAM 스캔 데이터와 BIM 모델을 시간의 흐름에 따라 결합한 데이터셋
**BCF 변환 가능성**: SLAM 스캔과 BIM 모델 간 차이점을 BCF 이슈로 변환 가능
**시계열 적합성**: 높음 - 시간에 따른 건물 변화 추적 가능
**신뢰도 기여**: 실제 건물 데이터로 높은 신뢰도
**접근성**: GitHub 리포지토리 접근 불가

## 2. DURAARK Dataset

**기관**: European Union FP7 Project
**설명**: 실제 건설 프로젝트에서 추출한 다분야 IFC 모델 집합
**BCF 변환 가능성**: 분야별 IFC 모델 간 충돌 검출 → BCF 이슈 변환
**시계열 적합성**: 중간 - 프로젝트 단계별 모델 비교 가능
**신뢰도 기여**: 실제 건설 프로젝트로 높은 신뢰도
**접근성**: 웹사이트 접근 가능

## 3. Schependomlaan Dataset (TU Eindhoven)

**기관**: TU Eindhoven
**설명**: 실제 주택 건설 프로젝트의 주차별 BIM 모델과 실제 BCF 2.0 파일
**BCF 변환 가능성**: 이미 BCF 파일이 있어서 직접 사용 가능
**시계열 적합성**: 매우 높음 - 주차별 모델과 BCF 이슈 추적
**신뢰도 기여**: 실제 BCF 파일로 최고 신뢰도
**접근성**: TU Eindhoven 웹사이트 접근 가능

## 4. 우선순위 및 추천사항

**1순위**: schependomlaan - 실제 BCF 파일 포함
**2순위**: slabim - 시간적 변화 추적 우수
**3순위**: duraark - IFC 모델 풍부

### 추천사항

- 1. Schependomlaan 데이터셋을 최우선으로 확보 - 실제 BCF 파일 포함
- 2. SLABIM 데이터셋을 2순위로 확보 - 시간적 변화 추적에 최적
- 3. DURAARK 데이터셋을 3순위로 확보 - IFC 모델 다양성 제공
- 4. 각 데이터셋에 대해 학술 기관에 직접 문의하여 접근 방법 확인
- 5. 데이터 확보 후 기존 97% 합성 데이터 비율을 80% 이하로 개선
- 6. 실제 BCF 파일 확보로 연구 신뢰도 대폭 향상 기대
