"""Mini NPU Simulator: MAC 연산 및 패턴 판별 시뮬레이터.

표준 라이브러리(json, time, pathlib, sys)만 사용하여 구현한 콘솔 애플리케이션입니다.
- 필수 기능:
  1. n×n 2차원 패턴/필터 데이터 구조 (Grid2D: 특정 위치 값 저장 및 읽기 지원)
  2. 모드 1: 3×3 사용자 입력 (필터 A/B, 패턴 입력 및 행/열/숫자 검증, MAC 연산, 판정, 성능 측정)
  3. 모드 2: data.json 분석 (필터/패턴 로드, 스키마/크기 검증, 라벨 정규화, epsilon 동점 판정, 성능 분석, 결과 리포트)
- 보너스 기능:
  1. 시뮬레이터 최적화(메모리 접근): 2차원 배열(N×N)을 1차원 배열(길이 N²)로 변환하여 최적화 전/후 성능 비교
  2. 패턴 생성기: 임의의 크기 N 입력 시 N×N 십자가(Cross)와 X 패턴 자동 생성 및 재활용
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

EPSILON: float = 1e-9
DEFAULT_REPEAT: int = 10
BENCHMARK_SIZES: tuple[int, ...] = (3, 5, 13, 25)


class Grid2D:
    """n×n 크기의 2차원 패턴 및 필터를 저장하고 관리하는 클래스."""

    def __init__(self, size: int, data: list[list[float]] | None = None) -> None:
        if size <= 0:
            raise ValueError(f"크기(size)는 1 이상이어야 합니다: {size}")
        self.size: int = size
        if data is None:
            self._grid: list[list[float]] = [
                [0.0 for _ in range(size)] for _ in range(size)
            ]
        else:
            self._validate_and_store(size, data)

    def _validate_and_store(self, size: int, data: Any) -> None:
        """2차원 리스트의 행/열 크기 및 숫자 타입을 검증하고 저장한다."""
        if not isinstance(data, list) or len(data) != size:
            actual_rows = len(data) if isinstance(data, list) else type(data).__name__
            raise ValueError(
                f"행 개수 불일치 (기대: {size}행, 실제: {actual_rows})"
            )
        parsed_grid: list[list[float]] = []
        for r_idx, row in enumerate(data):
            if not isinstance(row, list) or len(row) != size:
                actual_cols = len(row) if isinstance(row, list) else type(row).__name__
                raise ValueError(
                    f"{r_idx + 1}번째 행의 열 개수 불일치 (기대: {size}열, 실제: {actual_cols})"
                )
            parsed_row: list[float] = []
            for c_idx, val in enumerate(row):
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    try:
                        parsed_val = float(val)
                    except (ValueError, TypeError) as exc:
                        raise ValueError(
                            f"({r_idx}, {c_idx}) 위치의 값을 숫자로 변환할 수 없습니다: {val!r}"
                        ) from exc
                else:
                    parsed_val = float(val)
                parsed_row.append(parsed_val)
            parsed_grid.append(parsed_row)
        self._grid = parsed_grid

    def get(self, row: int, col: int) -> float:
        """특정 위치 (row, col)의 값을 읽어온다."""
        if not (0 <= row < self.size and 0 <= col < self.size):
            raise IndexError(f"인덱스 범위 초과: ({row}, {col}), 크기: {self.size}×{self.size}")
        return self._grid[row][col]

    def set(self, row: int, col: int, value: float) -> None:
        """특정 위치 (row, col)에 값을 저장한다."""
        if not (0 <= row < self.size and 0 <= col < self.size):
            raise IndexError(f"인덱스 범위 초과: ({row}, {col}), 크기: {self.size}×{self.size}")
        self._grid[row][col] = float(value)

    def to_2d_list(self) -> list[list[float]]:
        """내부 2차원 배열 복사본을 반환한다."""
        return [row[:] for row in self._grid]

    def to_1d_list(self) -> list[float]:
        """[보너스] 2차원 배열(N×N)을 1차원 배열(길이 N²)로 평탄화(flatten)하여 반환한다."""
        flat: list[float] = []
        for row in self._grid:
            for val in row:
                flat.append(val)
        return flat

    def format_pretty(self) -> str:
        """콘솔 확인용 문자열 포맷을 반환한다."""
        lines: list[str] = []
        for row in self._grid:
            formatted_vals = [
                f"{int(v)}" if v.is_integer() else f"{v:g}" for v in row
            ]
            lines.append(" ".join(formatted_vals))
        return "\n".join(lines)


# =====================================================================
# 보너스 과제: 패턴 생성기 (N×N Cross / X 패턴 자동 생성)
# =====================================================================
def generate_cross_pattern(n: int) -> Grid2D:
    """크기 N 입력 시 N×N 십자가(Cross) 패턴을 자동 생성한다."""
    grid = Grid2D(n)
    mid = n // 2
    for r in range(n):
        for c in range(n):
            if r == mid or c == mid:
                grid.set(r, c, 1.0)
    return grid


def generate_x_pattern(n: int) -> Grid2D:
    """크기 N 입력 시 N×N X 패턴을 자동 생성한다."""
    grid = Grid2D(n)
    for r in range(n):
        for c in range(n):
            if r == c or (r + c == n - 1):
                grid.set(r, c, 1.0)
    return grid


# =====================================================================
# 라벨 정규화 (표준 라벨: Cross, X)
# =====================================================================
def normalize_label(raw_label: Any) -> str:
    """입력 라벨이나 필터 키를 표준 라벨('Cross' 또는 'X')로 정규화한다.

    규칙:
      - expected 값: '+' -> 'Cross', 'x' -> 'X' (대소문자 및 'cross' 포함)
      - filter 키: 'cross' -> 'Cross', 'x' -> 'X'
    """
    if not isinstance(raw_label, str):
        raise ValueError(f"라벨이 문자열이 아닙니다: {raw_label!r}")
    cleaned = raw_label.strip().lower()
    if cleaned in ("+", "cross"):
        return "Cross"
    if cleaned == "x":
        return "X"
    raise ValueError(f"알 수 없는 라벨 형식입니다: {raw_label!r} (허용: '+', 'cross', 'x')")


# =====================================================================
# MAC (Multiply-Accumulate) 연산 (외부 라이브러리 없이 직접 구현)
# =====================================================================
def mac_compute_2d(pattern: Grid2D, filter_grid: Grid2D) -> float:
    """2차원 패턴과 필터의 위치별 곱셈 누적합(MAC)을 이중 반복문으로 계산한다."""
    if pattern.size != filter_grid.size:
        raise ValueError(
            f"패턴 크기({pattern.size}×{pattern.size})와 "
            f"필터 크기({filter_grid.size}×{filter_grid.size})가 일치하지 않습니다."
        )
    n = pattern.size
    total: float = 0.0
    for r in range(n):
        for c in range(n):
            total += pattern.get(r, c) * filter_grid.get(r, c)
    return total


def mac_compute_1d(pattern_1d: list[float], filter_1d: list[float]) -> float:
    """[보너스 최적화] 1차원 배열(길이 N²)로 변환된 패턴과 필터의 MAC 연산을 단일 루프로 수행한다."""
    if len(pattern_1d) != len(filter_1d):
        raise ValueError(
            f"1차원 배열 길이 불일치 (패턴: {len(pattern_1d)}, 필터: {len(filter_1d)})"
        )
    total: float = 0.0
    length = len(pattern_1d)
    for i in range(length):
        total += pattern_1d[i] * filter_1d[i]
    return total


# =====================================================================
# 점수 비교 정책 (허용오차 epsilon 기반 동점 처리)
# =====================================================================
def compare_scores(
    score_a: float,
    score_b: float,
    label_a: str = "Cross",
    label_b: str = "X",
    undecided_label: str = "UNDECIDED",
    epsilon: float = EPSILON,
) -> str:
    """허용오차(epsilon) 기반으로 두 점수를 비교하여 판정 라벨을 반환한다."""
    if abs(score_a - score_b) < epsilon:
        return undecided_label
    return label_a if score_a > score_b else label_b


def format_score(score: float) -> str:
    """일반 판정 케이스의 점수를 깔끔한 소수 형식으로 포맷한다."""
    rounded = round(score, 9)
    if abs(rounded - round(rounded)) < 1e-9:
        return f"{round(rounded):.1f}"
    return f"{rounded:g}"


# =====================================================================
# 성능 측정 함수 (I/O 제외, 순수 연산 구간 반복 측정)
# =====================================================================
def measure_mac_2d_ms(
    pattern: Grid2D,
    filter_grid: Grid2D,
    repeat: int = DEFAULT_REPEAT,
) -> tuple[float, float]:
    """2D MAC 연산을 repeat 회 반복 측정하여 (최종 점수, 평균 소요 시간 ms)를 반환한다."""
    score: float = 0.0
    start_ns = time.perf_counter_ns()
    for _ in range(repeat):
        score = mac_compute_2d(pattern, filter_grid)
    elapsed_ns = time.perf_counter_ns() - start_ns
    avg_ms = (elapsed_ns / 1_000_000.0) / repeat
    return score, avg_ms


def measure_mac_1d_ms(
    pattern_1d: list[float],
    filter_1d: list[float],
    repeat: int = DEFAULT_REPEAT,
) -> tuple[float, float]:
    """[보너스] 1D 평탄화 배열 MAC 연산을 repeat 회 반복 측정하여 (점수, 평균 시간 ms)를 반환한다."""
    score: float = 0.0
    start_ns = time.perf_counter_ns()
    for _ in range(repeat):
        score = mac_compute_1d(pattern_1d, filter_1d)
    elapsed_ns = time.perf_counter_ns() - start_ns
    avg_ms = (elapsed_ns / 1_000_000.0) / repeat
    return score, avg_ms


def print_performance_table(
    sizes: tuple[int, ...] = BENCHMARK_SIZES,
    repeat: int = DEFAULT_REPEAT,
    custom_filters: dict[int, dict[str, Grid2D]] | None = None,
) -> None:
    """크기별 평균 연산 시간(ms)과 연산 횟수(N²) 표 및 1D 최적화 비교 표를 출력한다."""
    print(f"#---------------------------------------")
    print(f"# [3] 성능 분석 (평균/{repeat}회)")
    print(f"#---------------------------------------")
    print(f"{'크기':<8} {'평균 시간(ms)':<16} {'연산 횟수'}")
    print("-" * 40)

    opt_records: list[tuple[int, float, float, int]] = []

    for n in sizes:
        if custom_filters and n in custom_filters and "Cross" in custom_filters[n]:
            f_grid = custom_filters[n]["Cross"]
        else:
            f_grid = generate_cross_pattern(n)
        p_grid = generate_cross_pattern(n)

        _, avg_2d_ms = measure_mac_2d_ms(p_grid, f_grid, repeat=repeat)

        p_1d = p_grid.to_1d_list()
        f_1d = f_grid.to_1d_list()
        _, avg_1d_ms = measure_mac_1d_ms(p_1d, f_1d, repeat=repeat)

        ops = n * n
        size_label = f"{n}×{n}"
        print(f"{size_label:<8} {avg_2d_ms:<16.4f} {ops}")
        opt_records.append((n, avg_2d_ms, avg_1d_ms, ops))

    print("\n[보너스: 2D 배열 vs 1D 평탄화 배열(길이 N²) 메모리 접근 최적화 비교]")
    print(f"{'크기':<8} {'2D 평균(ms)':<14} {'1D 평균(ms)':<14} {'속도 향상률':<12} {'연산 횟수(N²)'}")
    print("-" * 66)
    for n, t_2d, t_1d, ops in opt_records:
        speedup = ((t_2d - t_1d) / t_2d * 100.0) if t_2d > 0 else 0.0
        size_label = f"{n}×{n}"
        print(f"{size_label:<8} {t_2d:<14.4f} {t_1d:<14.4f} {speedup:>6.1f}%      {ops}")


# =====================================================================
# 모드 1: 사용자 입력 (3×3)
# =====================================================================
def read_grid_from_console(title: str, size: int = 3, default_kind: str | None = None) -> Grid2D:
    """콘솔에서 size×size 행렬을 한 줄씩(공백 구분) 입력받아 검증 후 Grid2D로 반환한다.

    입력 검증:
      - 각 줄에 정확히 size개의 숫자가 공백으로 구분되어 있어야 한다.
      - 전체 행렬을 다시 입력받거나 줄 단위로 재입력을 유도하여 행/열 불일치 및 숫자 파싱 오류를 방어한다.
      - 보너스 기능: 첫 줄에 'auto' 입력 시 패턴 생성기로 자동 생성 지원.
    """
    while True:
        print(f"{title} ({size}줄 입력, 공백 구분)")
        grid = Grid2D(size)
        restart_matrix = False

        for r in range(size):
            while True:
                try:
                    raw_line = input()
                except EOFError as exc:
                    raise KeyboardInterrupt("입력이 종료되었습니다.") from exc

                stripped = raw_line.strip()
                if r == 0 and stripped.lower() == "auto" and default_kind in ("cross", "x"):
                    auto_grid = (
                        generate_cross_pattern(size)
                        if default_kind == "cross"
                        else generate_x_pattern(size)
                    )
                    print(f"  -> [패턴 생성기] {size}×{size} {default_kind.upper()} 패턴이 자동 생성되었습니다:")
                    print(auto_grid.format_pretty())
                    return auto_grid

                if not stripped:
                    print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
                    continue

                tokens = stripped.split()
                if len(tokens) != size:
                    print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
                    continue

                parsed_vals: list[float] = []
                parse_error = False
                for token in tokens:
                    try:
                        parsed_vals.append(float(token))
                    except ValueError:
                        parse_error = True
                        break

                if parse_error:
                    print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
                    continue

                for c, val in enumerate(parsed_vals):
                    grid.set(r, c, val)
                break

            if restart_matrix:
                break

        if not restart_matrix:
            return grid


def run_mode_1() -> None:
    """모드 1: 3×3 사용자 입력 모드를 순서대로 실행한다."""
    size = 3
    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    filter_a = read_grid_from_console("필터 A", size=size, default_kind="cross")
    print()
    filter_b = read_grid_from_console("필터 B", size=size, default_kind="x")
    print(f"\n✓ 3×3 필터 A, B 저장 완료")

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = read_grid_from_console("패턴", size=size, default_kind="x")

    # MAC 연산 및 10회 반복 평균 시간 측정
    score_a, avg_a_ms = measure_mac_2d_ms(pattern, filter_a, repeat=DEFAULT_REPEAT)
    score_b, avg_b_ms = measure_mac_2d_ms(pattern, filter_b, repeat=DEFAULT_REPEAT)
    avg_total_ms = (avg_a_ms + avg_b_ms) / 2.0

    verdict = compare_scores(
        score_a,
        score_b,
        label_a="A",
        label_b="B",
        undecided_label="판정 불가 (|A-B| < 1e-9)",
        epsilon=EPSILON,
    )

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    if verdict.startswith("판정 불가"):
        print(f"A 점수: {score_a:.16f}")
        print(f"B 점수: {score_b:.16f}")
    else:
        print(f"A 점수: {format_score(score_a)}")
        print(f"B 점수: {format_score(score_b)}")
    print(f"연산 시간(평균/{DEFAULT_REPEAT}회): {avg_total_ms:.3f} ms")
    print(f"판정: {verdict}")

    print()
    print_performance_table(
        sizes=(3,),
        repeat=DEFAULT_REPEAT,
        custom_filters={3: {"Cross": filter_a, "X": filter_b}},
    )


# =====================================================================
# 모드 2: data.json 로드, 스키마/크기 검증 및 일괄 분석
# =====================================================================
def find_data_json(custom_path: str | None = None) -> Path:
    """data.json 파일 경로를 탐색한다."""
    if custom_path:
        p = Path(custom_path)
        if p.is_file():
            return p

    candidates = [
        Path.cwd() / "data.json",
        Path(__file__).resolve().parent / "data.json",
        Path.cwd().parent / "data.json",
        Path.home() / "Downloads" / "data.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return Path(__file__).resolve().parent / "data.json"


def parse_size_from_key(key: str) -> int:
    """'size_5' 또는 'size_5_1' 형태의 키에서 정수 N(크기)을 추출한다."""
    parts = key.strip().split("_")
    if len(parts) < 2 or parts[0] != "size":
        raise ValueError(f"키 형식이 'size_{{N}}' 규칙에 맞지 않습니다: {key!r}")
    try:
        n = int(parts[1])
    except ValueError as exc:
        raise ValueError(f"키에서 크기(N)를 정수로 추출할 수 없습니다: {key!r}") from exc
    if n <= 0:
        raise ValueError(f"유효하지 않은 크기(N): {n}")
    return n


def run_mode_2(json_path_str: str | None = None) -> None:
    """모드 2: data.json을 로드하여 필터/패턴 검증, MAC 연산, 성능 분석, 결과 요약을 출력한다."""
    data_path = find_data_json(json_path_str)
    if not data_path.is_file():
        print(f"\n[오류] 데이터 파일을 찾을 수 없습니다: {data_path}")
        return

    try:
        raw_text = data_path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        print(f"\n[오류] data.json JSON 파싱 실패: {exc}")
        return
    except OSError as exc:
        print(f"\n[오류] data.json 파일 읽기 실패: {exc}")
        return

    if not isinstance(payload, dict):
        print("\n[오류] data.json 최상위 구조는 JSON 객체(dict)여야 합니다.")
        return

    raw_filters = payload.get("filters")
    raw_patterns = payload.get("patterns")
    if not isinstance(raw_filters, dict) or not isinstance(raw_patterns, dict):
        print("\n[오류] data.json에 'filters' 또는 'patterns' 객체가 누락되었거나 형식이 올바르지 않습니다.")
        return

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")

    loaded_filters: dict[int, dict[str, Grid2D]] = {}
    filter_errors: dict[int, str] = {}

    for f_key, f_group in raw_filters.items():
        try:
            n = parse_size_from_key(f_key)
        except ValueError as exc:
            print(f"✗ {f_key} 필터 로드 실패: {exc}")
            continue

        if not isinstance(f_group, dict):
            filter_errors[n] = f"{f_key} 필터 데이터가 객체(dict) 형식이 아닙니다."
            print(f"✗ {f_key} 필터 로드 실패: {filter_errors[n]}")
            continue

        normalized_pair: dict[str, Grid2D] = {}
        err_msg: str | None = None
        for raw_label, matrix_data in f_group.items():
            try:
                std_label = normalize_label(raw_label)
                grid = Grid2D(n, matrix_data)
                normalized_pair[std_label] = grid
            except ValueError as exc:
                err_msg = f"필터 '{f_key}.{raw_label}' 검증 오류: {exc}"
                break

        if err_msg:
            filter_errors[n] = err_msg
            print(f"✗ {f_key} 필터 로드 실패 ({err_msg})")
        elif "Cross" not in normalized_pair or "X" not in normalized_pair:
            missing = [lbl for lbl in ("Cross", "X") if lbl not in normalized_pair]
            filter_errors[n] = f"필수 표준 필터 누락: {', '.join(missing)}"
            print(f"✗ {f_key} 필터 로드 실패 ({filter_errors[n]})")
        else:
            loaded_filters[n] = normalized_pair
            print(f"✓ {f_key} 필터 로드 완료 (Cross, X)")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")

    total_count = 0
    pass_count = 0
    fail_count = 0
    fail_cases: list[tuple[str, str]] = []

    for p_key, p_item in raw_patterns.items():
        total_count += 1
        print(f"--- {p_key} ---")

        # 1) 패턴 키에서 크기 N 추출
        try:
            n = parse_size_from_key(p_key)
        except ValueError as exc:
            reason = f"패턴 키 형식 오류 ({exc})"
            print(f"판정: ERROR | FAIL ({reason})")
            fail_count += 1
            fail_cases.append((p_key, reason))
            continue

        # 2) 해당 size_N 필터 존재 여부 확인
        if n in filter_errors:
            reason = f"size_{n} 필터 오류로 판정 불가 ({filter_errors[n]})"
            print(f"판정: ERROR | FAIL ({reason})")
            fail_count += 1
            fail_cases.append((p_key, reason))
            continue

        if n not in loaded_filters:
            reason = f"size_{n} 필터가 data.json에 존재하지 않음"
            print(f"판정: ERROR | FAIL ({reason})")
            fail_count += 1
            fail_cases.append((p_key, reason))
            continue

        # 3) 패턴 항목 스키마 검증
        if not isinstance(p_item, dict):
            reason = "패턴 데이터가 객체(dict) 형식이 아님"
            print(f"판정: ERROR | FAIL ({reason})")
            fail_count += 1
            fail_cases.append((p_key, reason))
            continue

        if "input" not in p_item or "expected" not in p_item:
            reason = "패턴 데이터에 'input' 또는 'expected' 키가 누락됨"
            print(f"판정: ERROR | FAIL ({reason})")
            fail_count += 1
            fail_cases.append((p_key, reason))
            continue

        # 4) expected 라벨 정규화 검증
        try:
            expected_std = normalize_label(p_item["expected"])
        except ValueError as exc:
            reason = f"expected 라벨 정규화 실패 ({exc})"
            print(f"판정: ERROR | FAIL ({reason})")
            fail_count += 1
            fail_cases.append((p_key, reason))
            continue

        # 5) 패턴 크기(N×N) 및 숫자 데이터 검증 (필터 크기와 일치 여부 확인)
        try:
            pattern_grid = Grid2D(n, p_item["input"])
        except ValueError as exc:
            reason = f"필터({n}×{n})와 패턴 크기/형식 불일치: {exc}"
            print(f"판정: ERROR | expected: {expected_std} | FAIL ({reason})")
            fail_count += 1
            fail_cases.append((p_key, reason))
            continue

        cross_filter = loaded_filters[n]["Cross"]
        x_filter = loaded_filters[n]["X"]

        if pattern_grid.size != cross_filter.size or pattern_grid.size != x_filter.size:
            reason = (
                f"패턴 크기({pattern_grid.size}×{pattern_grid.size})와 "
                f"필터 크기({cross_filter.size}×{cross_filter.size}) 불일치"
            )
            print(f"판정: ERROR | expected: {expected_std} | FAIL ({reason})")
            fail_count += 1
            fail_cases.append((p_key, reason))
            continue

        # 6) MAC 연산 수행
        score_cross = mac_compute_2d(pattern_grid, cross_filter)
        score_x = mac_compute_2d(pattern_grid, x_filter)

        # 7) epsilon 기반 점수 비교 및 판정
        prediction = compare_scores(
            score_cross,
            score_x,
            label_a="Cross",
            label_b="X",
            undecided_label="UNDECIDED",
            epsilon=EPSILON,
        )

        if prediction == "UNDECIDED":
            print(f"Cross 점수: {score_cross:.16f}")
            print(f"X 점수: {score_x:.16f}")
        else:
            print(f"Cross 점수: {format_score(score_cross)}")
            print(f"X 점수: {format_score(score_x)}")

        if prediction == expected_std:
            pass_count += 1
            print(f"판정: {prediction} | expected: {expected_std} | PASS")
        else:
            fail_count += 1
            if prediction == "UNDECIDED":
                reason_short = "동점 규칙"
                reason_detail = (
                    f"동점(UNDECIDED) 처리 규칙(|Cross-X| = {abs(score_cross - score_x):.2e} < {EPSILON:.0e})에 따라 FAIL"
                )
            else:
                reason_short = "판정 불일치"
                reason_detail = f"판정({prediction})이 expected({expected_std})와 불일치하여 FAIL"
            print(f"판정: {prediction} | expected: {expected_std} | FAIL ({reason_short})")
            fail_cases.append((p_key, reason_detail))

    print()
    print_performance_table(
        sizes=BENCHMARK_SIZES,
        repeat=DEFAULT_REPEAT,
        custom_filters=loaded_filters,
    )

    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {total_count}개")
    print(f"통과: {pass_count}개")
    print(f"실패: {fail_count}개")
    if fail_cases:
        print("실패 케이스:")
        for case_id, reason in fail_cases:
            print(f"- {case_id}: {reason}")
    else:
        print("실패 케이스: 없음 (모든 케이스가 라벨 정규화 및 epsilon 비교 정책을 통과함)")
    print('(상세 원인 분석 및 복잡도 설명은 README.md의 "결과 리포트" 섹션에 작성)')


# =====================================================================
# 보너스 모드: 패턴 생성기 & 2D vs 1D 최적화 벤치마크
# =====================================================================
def run_bonus_pattern_generator() -> None:
    """[보너스 과제] 크기 N을 입력받아 N×N Cross/X 패턴을 자동 생성하고 MAC 연산 및 최적화를 테스트한다."""
    print("\n#---------------------------------------")
    print("# [보너스] N×N 패턴 생성기 및 최적화 비교")
    print("#---------------------------------------")
    while True:
        raw_n = input("생성할 패턴 크기 N을 입력하세요 (3 이상의 홀수 권장, 예: 5): ").strip()
        try:
            n = int(raw_n)
            if n < 3:
                print("크기 N은 3 이상의 정수로 입력하세요.")
                continue
            break
        except ValueError:
            print("유효한 정수를 입력하세요.")

    cross_grid = generate_cross_pattern(n)
    x_grid = generate_x_pattern(n)

    print(f"\n[자동 생성된 {n}×{n} Cross 패턴]")
    print(cross_grid.format_pretty())
    print(f"\n[자동 생성된 {n}×{n} X 패턴]")
    print(x_grid.format_pretty())

    score_cc = mac_compute_2d(cross_grid, cross_grid)
    score_cx = mac_compute_2d(cross_grid, x_grid)
    print(f"\n[검증] Cross 입력 vs Cross 필터 점수: {format_score(score_cc)}")
    print(f"[검증] Cross 입력 vs X 필터 점수: {format_score(score_cx)}")
    print(
        f"[판정] {compare_scores(score_cc, score_cx, 'Cross', 'X', 'UNDECIDED', EPSILON)}"
    )
    print()
    print_performance_table(sizes=(n,), repeat=100)


def main() -> None:
    """메인 실행 함수: 모드 선택 및 순서대로 흐름 실행."""
    print("=== Mini NPU Simulator ===")
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    print("3. [보너스] 패턴 생성기 (N×N 자동 생성 및 최적화 테스트)")

    while True:
        try:
            choice = input("선택: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n프로그램을 종료합니다.")
            return

        if choice == "1":
            try:
                run_mode_1()
            except KeyboardInterrupt:
                print("\n사용자 입력이 중단되었습니다.")
            break
        if choice == "2":
            run_mode_2()
            break
        if choice == "3":
            try:
                run_bonus_pattern_generator()
            except KeyboardInterrupt:
                print("\n사용자 입력이 중단되었습니다.")
            break

        print("입력 오류: 1, 2, 3 중에서 선택해 입력하세요.")


if __name__ == "__main__":
    main()

