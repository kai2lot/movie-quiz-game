"""나만의 영화 퀴즈 게임 메인 실행 파일."""

from quiz_game import QuizGame


def main() -> None:
    """QuizGame 인스턴스를 생성하고 게임을 시작한다."""
    game = QuizGame()
    game.run()


if __name__ == "__main__":
    main()
