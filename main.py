"""나만의 영화 퀴즈 게임 메인 실행 파일."""


def get_int_input(prompt: str, min_val: int, max_val: int) -> int:
    """사용자로부터 지정된 범위 내의 정수 입력을 안전하게 받는다."""
    while True:
        raw = input(prompt).strip()
        if not raw:
            print(f"⚠️ 빈 입력입니다. {min_val}-{max_val} 사이의 숫자를 입력하세요.")
            continue
        try:
            value = int(raw)
        except ValueError:
            print(f"⚠️ 잘못된 입력입니다. {min_val}-{max_val} 사이의 숫자를 입력하세요.")
            continue

        if not (min_val <= value <= max_val):
            print(f"⚠️ 잘못된 입력입니다. {min_val}-{max_val} 사이의 숫자를 입력하세요.")
            continue
        return value


def get_non_empty_input(prompt: str) -> str:
    """사용자로부터 비어 있지 않은 문자열 입력을 받는다."""
    while True:
        text = input(prompt).strip()
        if not text:
            print("⚠️ 내용을 비워둘 수 없습니다. 다시 입력해주세요.")
            continue
        return text


def display_menu() -> None:
    """메인 메뉴 화면을 출력한다."""
    print("\n========================================")
    print("        🎬 나만의 영화 퀴즈 게임 🎬")
    print("========================================")
    print("1. 퀴즈 풀기")
    print("2. 퀴즈 추가")
    print("3. 퀴즈 목록")
    print("4. 점수 확인")
    print("5. 종료")
    print("========================================")


def main() -> None:
    """프로그램 메인 루프를 실행한다."""
    try:
        while True:
            display_menu()
            choice = get_int_input("선택: ", 1, 5)
            if choice == 1:
                print("\n[안내] 퀴즈 풀기 기능 준비 중입니다.")
            elif choice == 2:
                print("\n[안내] 퀴즈 추가 기능 준비 중입니다.")
            elif choice == 3:
                print("\n[안내] 퀴즈 목록 기능 준비 중입니다.")
            elif choice == 4:
                print("\n[안내] 점수 확인 기능 준비 중입니다.")
            elif choice == 5:
                print("\n👋 퀴즈 게임을 종료합니다. 이용해 주셔서 감사합니다!")
                break
    except (KeyboardInterrupt, EOFError):
        print("\n\n⚠️ 사용자 요청(Ctrl+C / EOF)으로 프로그램을 안전하게 종료합니다.")


if __name__ == "__main__":
    main()
