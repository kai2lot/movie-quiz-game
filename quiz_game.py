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
        """저장된 퀴즈를 출제하고 사용자의 정답을 채점하여 결과를 표시한다."""
        if not self.quizzes:
            print("\n⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해주세요!")
            return

        total = len(self.quizzes)
        correct_count = 0
        print(f"\n📝 퀴즈를 시작합니다! (총 {total}문제)")

        for idx, quiz in enumerate(self.quizzes, start=1):
            print("\n----------------------------------------")
            quiz.display(index=idx)
            user_answer = self.get_int_input("정답 입력 (1-4): ", 1, 4)
            if quiz.check_answer(user_answer):
                print("✅ 정답입니다!")
                correct_count += 1
            else:
                correct_text = quiz.choices[quiz.answer - 1]
                print(f"❌ 오답입니다! (정답: {quiz.answer}번 - {correct_text})")

        score = round((correct_count / total) * 100)
        self.has_played = True
        print("\n========================================")
        print(f"🏆 결과: {total}문제 중 {correct_count}문제 정답! ({score}점)")
        if score > self.best_score:
            self.best_score = score
            print("🎉 새로운 최고 점수입니다!")
        print("========================================")

    def add_quiz(self) -> None:
        """사용자로부터 문제, 선택지 4개, 정답 번호를 입력받아 새 퀴즈를 등록한다."""
        print("\n📌 새로운 퀴즈를 추가합니다.")
        question = self.get_non_empty_input("문제를 입력하세요: ")
        choices: list[str] = []
        for idx in range(1, 5):
            choice = self.get_non_empty_input(f"선택지 {idx}: ")
            choices.append(choice)
        answer = self.get_int_input("정답 번호 (1-4): ", 1, 4)

        new_quiz = Quiz(question=question, choices=choices, answer=answer)
        self.quizzes.append(new_quiz)
        print("\n✅ 퀴즈가 추가되었습니다!")

    def list_quizzes(self) -> None:
        """등록된 퀴즈 목록을 화면에 출력한다."""
        if not self.quizzes:
            print("\n⚠️ 등록된 퀴즈가 없습니다.")
            return

        print(f"\n📋 등록된 퀴즈 목록 (총 {len(self.quizzes)}개)")
        print("----------------------------------------")
        for idx, quiz in enumerate(self.quizzes, start=1):
            print(f"[{idx}] {quiz.question}")
        print("----------------------------------------")

    def show_score(self) -> None:
        """최고 점수를 확인한다."""
        print("\n[안내] 점수 확인 기능 준비 중입니다.")
