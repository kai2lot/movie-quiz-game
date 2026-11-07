"""개별 퀴즈 데이터를 표현하고 관리하는 모듈."""


class Quiz:
    """개별 4지선다 퀴즈를 표현하는 클래스.

    Attributes:
        question: 퀴즈 문제 문자열.
        choices: 4개의 선택지 문자열 리스트.
        answer: 정답 번호 (1~4).
    """

    def __init__(self, question: str, choices: list[str], answer: int) -> None:
        """Quiz 인스턴스를 초기화한다."""
        if len(choices) != 4:
            raise ValueError("선택지는 반드시 4개여야 합니다.")
        if not (1 <= answer <= 4):
            raise ValueError("정답 번호는 1에서 4 사이여야 합니다.")
        self.question = question
        self.choices = choices
        self.answer = answer

    def display(self, index: int | None = None) -> None:
        """퀴즈 문제와 4개의 선택지를 화면에 출력한다."""
        if index is not None:
            print(f"\n[문제 {index}]")
        else:
            print()
        print(self.question)
        print()
        for idx, choice in enumerate(self.choices, start=1):
            print(f"{idx}. {choice}")
        print()

    def check_answer(self, user_answer: int) -> bool:
        """사용자가 입력한 번호가 정답인지 확인한다."""
        return self.answer == user_answer

    def to_dict(self) -> dict:
        """JSON 저장을 위해 Quiz 객체를 딕셔너리로 변환한다."""
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quiz":
        """딕셔너리 데이터로부터 Quiz 객체를 생성한다."""
        question = str(data["question"]).strip()
        choices = [str(c).strip() for c in data["choices"]]
        answer = int(data["answer"])
        if not question or any(not c for c in choices):
            raise ValueError("퀴즈 문제나 선택지가 비어 있습니다.")
        return cls(question=question, choices=choices, answer=answer)
