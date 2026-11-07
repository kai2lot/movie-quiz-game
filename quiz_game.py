"""퀴즈 게임 전체 흐름과 상태를 관리하는 모듈."""

from quiz import Quiz, get_default_quizzes


class QuizGame:
    """퀴즈 게임의 목록, 점수, 입력 및 실행 흐름을 관리하는 클래스."""

    def __init__(self) -> None:
        """QuizGame 인스턴스를 초기화한다."""
        self.quizzes: list[Quiz] = get_default_quizzes()
        self.best_score: int = 0
        self.has_played: bool = False

    @staticmethod
    def get_int_input(prompt: str, min_val: int, max_val: int) -> int:
        """지정된 범위(min_val ~ max_val) 내의 정수를 입력받아 반환한다."""
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

    @staticmethod
    def get_non_empty_input(prompt: str) -> str:
        """비어 있지 않은 문자열을 입력받아 반환한다."""
        while True:
            text = input(prompt).strip()
            if not text:
                print("⚠️ 내용을 비워둘 수 없습니다. 다시 입력해주세요.")
                continue
            return text

    def display_menu(self) -> None:
        """메인 메뉴를 화면에 출력한다."""
        print("\n========================================")
        print("        🎬 나만의 영화 퀴즈 게임 🎬")
        print("========================================")
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 점수 확인")
        print("5. 종료")
        print("========================================")

    def run(self) -> None:
        """퀴즈 게임 메인 루프를 실행한다."""
        try:
            while True:
                self.display_menu()
                choice = self.get_int_input("선택: ", 1, 5)
                if choice == 1:
                    self.play_quiz()
                elif choice == 2:
                    self.add_quiz()
                elif choice == 3:
                    self.list_quizzes()
                elif choice == 4:
                    self.show_score()
                elif choice == 5:
                    print("\n👋 퀴즈 게임을 종료합니다. 이용해 주셔서 감사합니다!")
                    break
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️ 입력이 중단되어 프로그램을 안전하게 종료합니다.")

    def play_quiz(self) -> None:
        """퀴즈 풀기 기능을 수행한다."""
        print("\n[안내] 퀴즈 풀기 기능 준비 중입니다.")

    def add_quiz(self) -> None:
        """새로운 퀴즈를 추가한다."""
        print("\n[안내] 퀴즈 추가 기능 준비 중입니다.")

    def list_quizzes(self) -> None:
        """등록된 퀴즈 목록을 출력한다."""
        print("\n[안내] 퀴즈 목록 기능 준비 중입니다.")

    def show_score(self) -> None:
        """최고 점수를 확인한다."""
        print("\n[안내] 점수 확인 기능 준비 중입니다.")
