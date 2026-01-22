# HƯỚNG DẪN SỬ DỤNG K_POST_MATURE

## Vấn đề
DEL curve tăng liên tục sau MOB 24 thay vì flatten, do:
- K values tăng dần đến 1.0 sau MOB 24
- Ngay cả khi P_m (transition matrix) đã ổn định, K cao vẫn gây slope tăng

## Giải pháp
Thêm parameter `K_POST_MATURE` trong `src/config.py` để cố định K cho MOB > TARGET_MOB.

## Cách sử dụng

### 1. Cấu hình trong `src/config.py`

```python
# K_POST_MATURE: Giá trị K sử dụng cho MOB > TARGET_MOB (sau khi mature)
# - Nếu K_POST_MATURE = None: Sử dụng K từ calibration (k_final_by_mob)
# - Nếu K_POST_MATURE = 0.3: Sử dụng K = 0.3 cho tất cả MOB > TARGET_MOB
# - Giá trị khuyến nghị: 0.3 - 0.5 (để giảm slope sau mature)
K_POST_MATURE = 0.3   # K value cho MOB > TARGET_MOB (None = dùng calibrated K)
```

### 2. Giá trị khuyến nghị

| K_POST_MATURE | Ý nghĩa |
|---------------|---------|
| `None` | Dùng K từ calibration (có thể cao) |
| `0.3` | Conservative - DEL curve flatten nhanh |
| `0.5` | Moderate - DEL curve tăng chậm |
| `0.7` | Aggressive - DEL curve vẫn tăng |

### 3. Notebooks đã được cập nhật

- ✅ `notebooks/Markovchain.ipynb`
- ✅ `notebooks/Markovchain_With_Diagnostic_Clean.ipynb`
- ✅ `notebooks/Final_Workflow.ipynb`

### 4. Logic áp dụng

```python
# Sau khi fit_alpha() trả về k_final_by_mob
if K_POST_MATURE is not None:
    for mob in range(TARGET_MOB + 1, MAX_MOB + 1):
        k_final_by_mob[mob] = K_POST_MATURE
```

## Ví dụ

Với `TARGET_MOBS = [24]` và `K_POST_MATURE = 0.3`:

| MOB | K (trước) | K (sau) |
|-----|-----------|---------|
| 24  | 0.65      | 0.65 ← (giữ nguyên) |
| 25  | 0.95      | 0.30 |
| 26  | 0.98      | 0.30 |
| ... | ...       | 0.30 |
| 36  | 1.00      | 0.30 |

## Tắt K_POST_MATURE

Nếu muốn dùng K từ calibration (không cap):

```python
K_POST_MATURE = None
```

## Xem thêm

- `GIAI_THICH_K_VALUES.md` - Giải thích tại sao K là vấn đề
- `TRA_LOI_CAU_HOI_K.md` - Trả lời câu hỏi về K
- `notebooks/Markovchain_With_Diagnostic_Clean.ipynb` - Notebook diagnostic
