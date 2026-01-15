# 🔬 Research: Phương pháp Allocation đúng cho Roll Rate Model

## 🚨 Vấn đề hiện tại

### Logic hiện tại (SAI)

```
Cohort: SALPIL × LOW × 2024-01 @ MOB 12
Lifecycle forecast:
- DPD0: 600 (80%)
- DPD30+: 150 (20%)

Loans trong cohort (tại snapshot 2024-12):
- LOAN_001: MOB_CURRENT = 11, STATE_CURRENT = DPD0
- LOAN_002: MOB_CURRENT = 11, STATE_CURRENT = DPD0
- LOAN_003: MOB_CURRENT = 11, STATE_CURRENT = DPD30+
...

Logic hiện tại:
→ Random assign: 80% loans → DPD0, 20% loans → DPD30+
→ LOAN_001 (đang DPD0) có thể bị assign DPD30+ với xác suất 20%
→ LOAN_003 (đang DPD30+) có thể bị assign DPD0 với xác suất 80%
```

### Tại sao SAI?

1. **Không xét STATE_CURRENT của loan**
   - Loan đang DPD0 có xác suất thấp để nhảy lên DPD30+ trong 1 tháng
   - Loan đang DPD30+ có xác suất cao để tiếp tục DPD30+ hoặc xấu hơn

2. **Không xét MOB_CURRENT của loan**
   - Loan MOB=1 gần như không thể DPD30+ (chưa đủ thời gian)
   - Loan MOB=11 có thể DPD30+ (đã có thời gian để delinquent)

3. **Random sampling không phản ánh thực tế**
   - Loan tốt (DPD0) bị assign xấu (DPD30+) → SAI
   - Loan xấu (DPD30+) bị assign tốt (DPD0) → SAI

---

## ✅ Giải pháp đúng: Dùng Transition Matrix

### Nguyên lý

**Thay vì random assign, dùng transition matrix để tính xác suất chuyển state:**

```
Loan LOAN_001:
- STATE_CURRENT = DPD0
- MOB_CURRENT = 11
- TARGET_MOB = 12 (forecast 1 tháng)

Transition matrix @ MOB 11→12:
| From/To  | DPD0 | DPD30+ | WRITEOFF |
|----------|------|--------|----------|
| DPD0     | 0.95 | 0.04   | 0.01     |
| DPD30+   | 0.10 | 0.70   | 0.20     |
| WRITEOFF | 0.00 | 0.00   | 1.00     |

→ LOAN_001 (đang DPD0):
  - P(DPD0) = 95%
  - P(DPD30+) = 4%
  - P(WRITEOFF) = 1%

→ LOAN_003 (đang DPD30+):
  - P(DPD0) = 10%
  - P(DPD30+) = 70%
  - P(WRITEOFF) = 20%
```

### Logic đúng

```python
def allocate_with_transition_matrix(
    df_loans_latest,      # Loan-level data với STATE_CURRENT
    matrices_by_mob,      # Transition matrices theo MOB
    target_mob,           # MOB cần forecast
):
    results = []
    
    for _, loan in df_loans_latest.iterrows():
        loan_id = loan['AGREEMENT_ID']
        state_current = loan['STATE_MODEL']  # STATE hiện tại
        mob_current = loan['MOB']            # MOB hiện tại
        ead_current = loan['PRINCIPLE_OUTSTANDING']
        
        # Số bước cần forecast
        steps = target_mob - mob_current
        
        if steps <= 0:
            # Loan đã qua target_mob → Dùng state hiện tại
            state_forecast = state_current
            ead_forecast = ead_current
        else:
            # Áp dụng transition matrix steps lần
            state_probs = {state_current: 1.0}  # Bắt đầu từ state hiện tại
            
            for step in range(steps):
                mob_step = mob_current + step
                matrix = matrices_by_mob.get(mob_step, default_matrix)
                
                # Nhân ma trận xác suất
                new_probs = {}
                for from_state, prob in state_probs.items():
                    for to_state, trans_prob in matrix[from_state].items():
                        new_probs[to_state] = new_probs.get(to_state, 0) + prob * trans_prob
                
                state_probs = new_probs
            
            # Assign state theo xác suất
            state_forecast = random.choices(
                list(state_probs.keys()),
                weights=list(state_probs.values())
            )[0]
            
            # Tính EAD forecast (giảm theo prepay/writeoff)
            ead_forecast = ead_current * (1 - state_probs.get('PREPAY', 0) - state_probs.get('WRITEOFF', 0))
        
        results.append({
            'AGREEMENT_ID': loan_id,
            'STATE_CURRENT': state_current,
            'MOB_CURRENT': mob_current,
            'STATE_FORECAST': state_forecast,
            'EAD_FORECAST': ead_forecast,
            'TARGET_MOB': target_mob,
        })
    
    return pd.DataFrame(results)
```

---

## 📊 So sánh 3 phương pháp

### Method 1: Random Sampling (Hiện tại - SAI)

```
Logic: Random assign state theo phân phối cohort
Ưu điểm: Đơn giản
Nhược điểm: 
  - Không xét STATE_CURRENT
  - Không xét MOB_CURRENT
  - Loan tốt có thể bị assign xấu
```

**Ví dụ:**
```
LOAN_001 (DPD0, MOB=11):
  → Random: 80% DPD0, 20% DPD30+
  → Có thể bị assign DPD30+ (SAI!)

LOAN_003 (DPD30+, MOB=11):
  → Random: 80% DPD0, 20% DPD30+
  → Có thể bị assign DPD0 (SAI!)
```

### Method 2: Transition Matrix (Đề xuất - ĐÚNG)

```
Logic: Dùng transition matrix để tính xác suất từ STATE_CURRENT
Ưu điểm:
  - Xét STATE_CURRENT
  - Xét MOB_CURRENT (matrix khác nhau theo MOB)
  - Phản ánh đúng hành vi thực tế
Nhược điểm:
  - Phức tạp hơn
  - Cần transition matrix
```

**Ví dụ:**
```
LOAN_001 (DPD0, MOB=11):
  → Transition: 95% DPD0, 4% DPD30+, 1% WRITEOFF
  → Hầu như chắc chắn DPD0 (ĐÚNG!)

LOAN_003 (DPD30+, MOB=11):
  → Transition: 10% DPD0, 70% DPD30+, 20% WRITEOFF
  → Hầu như chắc chắn DPD30+ hoặc xấu hơn (ĐÚNG!)
```

### Method 3: Deterministic (Đơn giản nhất)

```
Logic: Giữ nguyên STATE_CURRENT, chỉ tính EAD_FORECAST
Ưu điểm:
  - Rất đơn giản
  - Không cần random
Nhược điểm:
  - Không phản ánh chuyển state
  - Chỉ phù hợp cho short-term forecast
```

**Ví dụ:**
```
LOAN_001 (DPD0, MOB=11):
  → STATE_FORECAST = DPD0 (giữ nguyên)
  → EAD_FORECAST = EAD_CURRENT × ead_ratio

LOAN_003 (DPD30+, MOB=11):
  → STATE_FORECAST = DPD30+ (giữ nguyên)
  → EAD_FORECAST = EAD_CURRENT × ead_ratio
```

---

## 🎯 Đề xuất: Method 2 (Transition Matrix)

### Lý do chọn

1. **Phản ánh đúng hành vi thực tế**
   - Loan DPD0 có xác suất cao giữ DPD0
   - Loan DPD30+ có xác suất cao tiếp tục xấu

2. **Đã có sẵn transition matrix**
   - `matrices_by_mob` từ `compute_transition_by_mob()`
   - Không cần tính toán thêm

3. **Consistency với lifecycle forecast**
   - Lifecycle dùng transition matrix
   - Allocation cũng nên dùng transition matrix

### Implementation

```python
def allocate_with_transition_matrix(
    df_loans_latest: pd.DataFrame,
    matrices_by_mob: dict,
    target_mob: int,
    parent_fallback: dict = None,
) -> pd.DataFrame:
    """
    Phân bổ forecast dựa trên transition matrix.
    
    Logic:
    1. Với mỗi loan, lấy STATE_CURRENT và MOB_CURRENT
    2. Áp dụng transition matrix từ MOB_CURRENT đến TARGET_MOB
    3. Tính xác suất state tại TARGET_MOB
    4. Assign state theo xác suất
    
    Parameters
    ----------
    df_loans_latest : DataFrame
        Loan-level data với STATE_MODEL, MOB, PRINCIPLE_OUTSTANDING
    matrices_by_mob : dict
        Transition matrices theo MOB: {mob: {from_state: {to_state: prob}}}
    target_mob : int
        MOB cần forecast
    parent_fallback : dict
        Fallback matrix nếu không có matrix cho MOB cụ thể
    
    Returns
    -------
    DataFrame
        Loan-level forecast với STATE_FORECAST, EAD_FORECAST
    """
    
    from src.config import CFG, BUCKETS_CANON
    
    loan_col = CFG["loan"]
    state_col = CFG["state"]
    mob_col = CFG["mob"]
    ead_col = CFG["ead"]
    
    results = []
    
    for _, loan in df_loans_latest.iterrows():
        loan_id = loan[loan_col]
        state_current = loan[state_col]
        mob_current = int(loan[mob_col])
        ead_current = float(loan[ead_col])
        
        # Số bước cần forecast
        steps = target_mob - mob_current
        
        if steps <= 0:
            # Loan đã qua target_mob → Giữ nguyên state
            state_forecast = state_current
            state_probs = {state_current: 1.0}
        else:
            # Bắt đầu từ state hiện tại
            state_probs = {state_current: 1.0}
            
            # Áp dụng transition matrix steps lần
            for step in range(steps):
                mob_step = mob_current + step
                
                # Lấy matrix cho MOB này
                matrix = matrices_by_mob.get(mob_step)
                if matrix is None and parent_fallback:
                    matrix = parent_fallback
                if matrix is None:
                    continue
                
                # Nhân ma trận xác suất
                new_probs = {st: 0.0 for st in BUCKETS_CANON}
                
                for from_state, prob in state_probs.items():
                    if prob <= 0 or from_state not in matrix:
                        continue
                    
                    for to_state, trans_prob in matrix[from_state].items():
                        if to_state in new_probs:
                            new_probs[to_state] += prob * trans_prob
                
                # Normalize
                total = sum(new_probs.values())
                if total > 0:
                    state_probs = {k: v/total for k, v in new_probs.items() if v > 0}
                else:
                    state_probs = {state_current: 1.0}
            
            # Assign state theo xác suất
            if state_probs:
                states = list(state_probs.keys())
                probs = list(state_probs.values())
                state_forecast = np.random.choice(states, p=probs)
            else:
                state_forecast = state_current
        
        # Tính EAD forecast
        # EAD giảm theo xác suất PREPAY + WRITEOFF + SOLDOUT
        absorbing_prob = (
            state_probs.get('PREPAY', 0) +
            state_probs.get('WRITEOFF', 0) +
            state_probs.get('SOLDOUT', 0)
        )
        ead_forecast = ead_current * (1 - absorbing_prob)
        
        results.append({
            loan_col: loan_id,
            'PRODUCT_TYPE': loan['PRODUCT_TYPE'],
            'RISK_SCORE': loan['RISK_SCORE'],
            'VINTAGE_DATE': loan['VINTAGE_DATE'],
            'STATE_CURRENT': state_current,
            'MOB_CURRENT': mob_current,
            'STATE_FORECAST': state_forecast,
            'EAD_CURRENT': ead_current,
            'EAD_FORECAST': ead_forecast,
            'TARGET_MOB': target_mob,
            'IS_FORECAST': 1,
        })
    
    return pd.DataFrame(results)
```

---

## 📊 Ví dụ so sánh

### Scenario: 3 loans trong cùng cohort

| Loan | STATE_CURRENT | MOB_CURRENT | EAD_CURRENT |
|------|---------------|-------------|-------------|
| L001 | DPD0          | 11          | 100         |
| L002 | DPD30+        | 11          | 100         |
| L003 | DPD0          | 5           | 100         |

**Target MOB = 12**

### Method 1: Random Sampling (SAI)

```
Cohort distribution @ MOB 12: 80% DPD0, 20% DPD30+

L001 (DPD0, MOB=11):
  → Random: 80% DPD0, 20% DPD30+
  → Có thể bị assign DPD30+ ❌

L002 (DPD30+, MOB=11):
  → Random: 80% DPD0, 20% DPD30+
  → Có thể bị assign DPD0 ❌

L003 (DPD0, MOB=5):
  → Random: 80% DPD0, 20% DPD30+
  → Có thể bị assign DPD30+ (7 bước!) ❌
```

### Method 2: Transition Matrix (ĐÚNG)

```
Transition matrix @ MOB 11→12:
| From/To  | DPD0 | DPD30+ | WRITEOFF |
|----------|------|--------|----------|
| DPD0     | 0.95 | 0.04   | 0.01     |
| DPD30+   | 0.10 | 0.70   | 0.20     |

L001 (DPD0, MOB=11):
  → 1 step: 95% DPD0, 4% DPD30+, 1% WRITEOFF
  → Hầu như chắc chắn DPD0 ✅

L002 (DPD30+, MOB=11):
  → 1 step: 10% DPD0, 70% DPD30+, 20% WRITEOFF
  → Hầu như chắc chắn DPD30+ hoặc xấu hơn ✅

L003 (DPD0, MOB=5):
  → 7 steps: Áp dụng matrix 7 lần
  → Xác suất DPD30+ tăng dần theo số bước
  → Nhưng vẫn thấp hơn L002 (đang DPD30+) ✅
```

---

## 🔧 Implementation Plan

### Bước 1: Tạo function mới

```python
# File: src/rollrate/allocation_v2.py

def allocate_with_transition_matrix(
    df_loans_latest,
    matrices_by_mob,
    target_mob,
    parent_fallback=None,
):
    # Implementation như trên
    pass
```

### Bước 2: Cập nhật allocation_multi_mob.py

```python
# Thay thế allocate_forecast_to_loans_simple
# bằng allocate_with_transition_matrix

df_allocated = allocate_with_transition_matrix(
    df_loans_latest=df_loans_latest,
    matrices_by_mob=matrices_by_mob,
    target_mob=target_mob,
    parent_fallback=parent_fallback,
)
```

### Bước 3: Cập nhật Complete_Workflow.ipynb

```python
# Truyền matrices_by_mob vào allocation
df_loan_forecast = allocate_multi_mob_with_del_metrics(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    matrices_by_mob=matrices_by_mob,  # NEW
    parent_fallback=parent_fallback,   # NEW
    target_mobs=[12, 24],
)
```

---

## ✅ Kết luận

### Vấn đề

Logic hiện tại (random sampling) **KHÔNG** xét:
- STATE_CURRENT của loan
- MOB_CURRENT của loan
- Transition probability

### Giải pháp

Dùng **Transition Matrix** để:
- Tính xác suất chuyển state từ STATE_CURRENT
- Áp dụng matrix nhiều lần (từ MOB_CURRENT đến TARGET_MOB)
- Assign state theo xác suất đúng

### Lợi ích

1. ✅ Loan DPD0 có xác suất cao giữ DPD0
2. ✅ Loan DPD30+ có xác suất cao tiếp tục xấu
3. ✅ Loan MOB thấp có xác suất thấp DPD30+
4. ✅ Consistency với lifecycle forecast

---

## 📚 Tài liệu tham khảo

1. [Roll Rate Analysis - ListenData](https://www.listendata.com/2019/09/roll-rate-analysis.html)
2. [Open Risk Manual - Roll Rates](https://www.openriskmanual.org/wiki/Roll_Rates)
3. [Markov Chain Credit Risk](https://riskwiki.vosesoftware.com/CreditratingsandMarkovChainmodels.php)
4. [Cohort Estimator](https://openriskmanual.org/wiki/Cohort_Estimator)

---

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-15  
**Version:** 1.0
