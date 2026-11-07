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


def get_default_quizzes() -> list[Quiz]:
    """초기 실행 및 데이터 복구 시 사용할 기본 영화 퀴즈 5개를 반환한다."""
    return [
        Quiz(
            question="마블 시네마틱 유니버스(MCU)에서 타노스가 모은 인피니티 스톤의 총 개수는?",
            choices=["4개", "5개", "6개", "7개"],
            answer=3,
        ),
        Quiz(
            question="한국 영화 최초로 칸 영화제 황금종려상과 아카데미 작품상을 동시에 수상한 영화 '기생충'의 감독은?",
            choices=["박찬욱", "봉준호", "나홍진", "류승완"],
            answer=2,
        ),
        Quiz(
            question="크리스토퍼 놀란 감독의 영화 '인터스텔라'에서 주인공 쿠퍼가 자녀 머피에게 메시지를 전달할 때 사용한 수단은?",
            choices=["손목시계 초침(모스 부호)", "라디오 주파수", "낡은 사진첩", "나침반 바늘"],
            answer=1,
        ),
        Quiz(
            question="영화 '매트릭스'에서 네오가 진실을 알게 되기 위해 모피어스에게서 받아 삼킨 알약의 색깔은?",
            choices=["파란색 알약", "초록색 알약", "빨간색 알약", "노란색 알약"],
            answer=3,
        ),
        Quiz(
            question="영화 '타이타닉'의 감독이자 '아바타' 시리즈를 연출한 세계적인 거장 감독은?",
            choices=["스티븐 스필버그", "제임스 카메론", "리들리 스콧", "피터 잭슨"],
            answer=2,
        ),
    ]

