"""퀴즈 게임 전체 흐름과 상태를 관리하는 모듈."""

from datetime import datetime
import json
from pathlib import Path
import random
from quiz import Quiz, get_default_quizzes


class QuizGame:
    """퀴즈 게임의 목록, 점수, 입력, 파일 저장 및 실행 흐름을 관리하는 클래스."""

    HINT_PENALTY: int = 5

    def __init__(self, state_file: str = "state.json") -> None:
        """QuizGame 인스턴스를 초기화하고 저장된 데이터를 불러온다."""
        self.state_path = Path(__file__).resolve().parent / state_file
        self.quizzes: list[Quiz] = []
        self.best_score: int = 0
        self.best_correct: int = 0
        self.best_total: int = 0
        self.has_played: bool = False
        self.history: list[dict] = []
        self.status_message: str = ""
        self.load_state()

    def load_state(self) -> None:
        """state.json 파일에서 퀴즈 목록, 최고 점수, 히스토리 데이터를 불러온다."""
        if not self.state_path.exists():
            self.quizzes = get_default_quizzes()
            self.best_score = 0
            self.best_correct = 0
            self.best_total = 0
            self.has_played = False
            self.history = []
            self.status_message = (
                f"📂 기본 퀴즈 데이터를 불러왔습니다. (퀴즈 {len(self.quizzes)}개)"
            )
            self.save_state()
            return

        try:
            with self.state_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict) or "quizzes" not in data or "best_score" not in data:
                raise ValueError("필수 키(quizzes, best_score)가 누락되었습니다.")

            raw_quizzes = data["quizzes"]
            if not isinstance(raw_quizzes, list):
                raise ValueError("quizzes 필드는 리스트 형태여야 합니다.")

            loaded_quizzes = [Quiz.from_dict(item) for item in raw_quizzes]
            best_score = int(data.get("best_score", 0))
            if best_score < 0:
                raise ValueError("best_score는 0 이상이어야 합니다.")

            raw_history = data.get("history", [])
            if not isinstance(raw_history, list):
                raise ValueError("history 필드는 리스트 형태여야 합니다.")

            self.quizzes = loaded_quizzes
            self.best_score = best_score
            self.best_correct = int(data.get("best_correct", 0))
            self.best_total = int(data.get("best_total", 0))
            self.history = raw_history
            self.has_played = bool(
                data.get("has_played", self.best_score > 0 or len(self.history) > 0)
            )
            self.status_message = (
                f"📂 저장된 데이터를 불러왔습니다. "
                f"(퀴즈 {len(self.quizzes)}개, 최고점수 {self.best_score}점)"
            )
        except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as err:
            print(
                f"\n⚠️ 데이터 파일({self.state_path.name})이 손상되었거나 읽을 수 없습니다 ({err}).\n"
                "🔄 기본 퀴즈 데이터로 복구 및 초기화합니다."
            )
            self.quizzes = get_default_quizzes()
            self.best_score = 0
            self.best_correct = 0
            self.best_total = 0
            self.has_played = False
            self.history = []
            self.status_message = (
                f"📂 기본 퀴즈 데이터로 복구되었습니다. (퀴즈 {len(self.quizzes)}개)"
            )
            self.save_state()

    def save_state(self) -> None:
        """현재 퀴즈 목록, 최고 점수, 히스토리 데이터를 state.json에 UTF-8로 저장한다."""
        data = {
            "quizzes": [q.to_dict() for q in self.quizzes],
            "best_score": self.best_score,
            "best_correct": self.best_correct,
            "best_total": self.best_total,
            "has_played": self.has_played,
            "history": self.history,
        }
        try:
            with self.state_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except OSError as err:
            print(f"⚠️ 데이터 파일 저장 중 오류가 발생했습니다: {err}")

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

    def display_menu(self, show_status: bool = False) -> None:
        """메인 메뉴를 화면에 출력한다."""
        print("\n========================================")
        print("        🎬 나만의 영화 퀴즈 게임 🎬")
        print("========================================")
        if show_status and self.status_message:
            print(self.status_message)
            print("========================================")
        print("1. 퀴즈 풀기 (랜덤 출제 / 문제 수 선택 / 힌트)")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 점수 및 히스토리 확인")
        print("5. 종료")
        print("6. 퀴즈 삭제 [보너스]")
        print("========================================")

    def run(self) -> None:
        """퀴즈 게임 메인 루프를 실행한다."""
        first_turn = True
        try:
            while True:
                self.display_menu(show_status=first_turn)
                first_turn = False
                choice = self.get_int_input("선택: ", 1, 6)
                if choice == 1:
                    self.play_quiz()
                elif choice == 2:
                    self.add_quiz()
                elif choice == 3:
                    self.list_quizzes()
                elif choice == 4:
                    self.show_score()
                elif choice == 5:
                    self.save_state()
                    print("\n💾 데이터를 저장했습니다.")
                    print("👋 퀴즈 게임을 종료합니다. 이용해 주셔서 감사합니다!")
                    break
                elif choice == 6:
                    self.delete_quiz()
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️ 사용자 요청(Ctrl+C / 입력 종료)이 감지되었습니다.")
            self.save_state()
            print("💾 현재까지의 진행 데이터를 안전하게 저장하고 종료합니다.")

    def _select_question_count(self, total_available: int) -> int:
        """풀고 싶은 문제 수를 입력받는다 (Enter 입력 시 전체 문제 출제)."""
        while True:
            raw = input(
                f"풀 문제 수를 입력하세요 (1-{total_available}, 그냥 Enter 입력 시 전체 {total_available}문제): "
            ).strip()
            if not raw:
                return total_available
            try:
                count = int(raw)
            except ValueError:
                print(f"⚠️ 잘못된 입력입니다. 1-{total_available} 사이의 숫자를 입력하세요.")
                continue

            if not (1 <= count <= total_available):
                print(f"⚠️ 잘못된 입력입니다. 1-{total_available} 사이의 숫자를 입력하세요.")
                continue
            return count

    def play_quiz(self) -> None:
        """저장된 퀴즈를 랜덤 순서로 출제하고, 힌트 및 정답을 처리하여 결과를 기록한다."""
        if not self.quizzes:
            print("\n⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해주세요!")
            return

        total_available = len(self.quizzes)
        print(f"\n📝 퀴즈 풀기 설정 (현재 등록된 퀴즈: 총 {total_available}문제)")
        selected_count = self._select_question_count(total_available)

        selected_quizzes = random.sample(self.quizzes, selected_count)
        correct_count = 0
        hint_used_count = 0

        print(
            f"\n📝 퀴즈를 시작합니다! (총 {selected_count}문제 랜덤 출제 | "
            f"풀이 중 '0' 입력 시 힌트 확인 가능, 힌트당 -{self.HINT_PENALTY}점)"
        )

        for idx, quiz in enumerate(selected_quizzes, start=1):
            print("\n----------------------------------------")
            quiz.display(index=idx)
            hint_shown_for_this_quiz = False

            while True:
                user_input = self.get_int_input("정답 입력 (1-4, 힌트 보기: 0): ", 0, 4)
                if user_input == 0:
                    if not hint_shown_for_this_quiz:
                        print(f"💡 [힌트] {quiz.hint} (-{self.HINT_PENALTY}점 차감 적용)")
                        hint_used_count += 1
                        hint_shown_for_this_quiz = True
                    else:
                        print(f"💡 [힌트 재확인] {quiz.hint} (이미 차감되었습니다)")
                    continue
                user_answer = user_input
                break

            if quiz.check_answer(user_answer):
                print("✅ 정답입니다!")
                correct_count += 1
            else:
                correct_text = quiz.choices[quiz.answer - 1]
                print(f"❌ 오답입니다! (정답: {quiz.answer}번 - {correct_text})")

        base_score = round((correct_count / selected_count) * 100)
        penalty = hint_used_count * self.HINT_PENALTY
        final_score = max(0, base_score - penalty)

        is_first_play = not self.has_played
        self.has_played = True

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append(
            {
                "played_at": now_str,
                "total_questions": selected_count,
                "correct_count": correct_count,
                "hints_used": hint_used_count,
                "score": final_score,
            }
        )

        print("\n========================================")
        if hint_used_count > 0:
            print(
                f"🏆 결과: {selected_count}문제 중 {correct_count}문제 정답! "
                f"(기본 {base_score}점 - 힌트 {hint_used_count}회 차감 {penalty}점 = 최종 {final_score}점)"
            )
        else:
            print(f"🏆 결과: {selected_count}문제 중 {correct_count}문제 정답! ({final_score}점)")

        if is_first_play or final_score > self.best_score:
            self.best_score = final_score
            self.best_correct = correct_count
            self.best_total = selected_count
            print("🎉 새로운 최고 점수입니다!")
        print("========================================")
        self.save_state()

    def add_quiz(self) -> None:
        """사용자로부터 문제, 선택지 4개, 정답 번호, 힌트를 입력받아 새 퀴즈를 등록한다."""
        print("\n📌 새로운 퀴즈를 추가합니다.")
        question = self.get_non_empty_input("문제를 입력하세요: ")
        choices: list[str] = []
        for idx in range(1, 5):
            choice = self.get_non_empty_input(f"선택지 {idx}: ")
            choices.append(choice)
        answer = self.get_int_input("정답 번호 (1-4): ", 1, 4)
        hint_raw = input("힌트를 입력하세요 (선택 사항, Enter로 건너뛰기 가능): ").strip()
        hint = hint_raw if hint_raw else "등록된 힌트가 없습니다."

        new_quiz = Quiz(question=question, choices=choices, answer=answer, hint=hint)
        self.quizzes.append(new_quiz)
        self.save_state()
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

    def delete_quiz(self) -> None:
        """등록된 퀴즈 중 선택한 번호의 퀴즈를 삭제하고 파일에 반영한다."""
        if not self.quizzes:
            print("\n⚠️ 삭제할 수 있는 퀴즈가 없습니다.")
            return

        self.list_quizzes()
        print("삭제할 퀴즈 번호를 입력하세요 (취소하려면 0 입력)")
        target_idx = self.get_int_input(f"번호 입력 (0-{len(self.quizzes)}): ", 0, len(self.quizzes))
        if target_idx == 0:
            print("↩️ 퀴즈 삭제를 취소했습니다.")
            return

        removed = self.quizzes.pop(target_idx - 1)
        self.save_state()
        print(f"\n🗑️ [{target_idx}] '{removed.question}' 퀴즈가 삭제되었습니다!")

    def show_score(self) -> None:
        """최고 점수와 전체 게임 플레이 기록 히스토리를 출력한다."""
        if not self.has_played and not self.history:
            print("\n📊 아직 퀴즈를 풀지 않았습니다. 퀴즈를 풀고 최고 점수에 도전해보세요!")
            return

        if self.best_total > 0:
            print(
                f"\n🏆 최고 점수: {self.best_score}점 "
                f"({self.best_total}문제 중 {self.best_correct}문제 정답)"
            )
        else:
            print(f"\n🏆 최고 점수: {self.best_score}점")

        if self.history:
            print(f"\n📜 점수 기록 히스토리 (총 {len(self.history)}회 플레이)")
            print("----------------------------------------")
            for idx, record in enumerate(self.history, start=1):
                played_at = record.get("played_at", "-")
                total_q = record.get("total_questions", 0)
                correct_q = record.get("correct_count", 0)
                hints = record.get("hints_used", 0)
                score = record.get("score", 0)
                hint_info = f", 힌트 {hints}회" if hints > 0 else ""
                print(
                    f"[{idx}] {played_at} | {total_q}문제 중 {correct_q}문제 정답{hint_info} -> {score}점"
                )
            print("----------------------------------------")
