from database.database import open_session
from database.models import User


def add_user(user_id: int, username: str) -> None:
    with open_session() as session:
        new_user = User(id=user_id, username=username)
        session.add(new_user)


def get_user(user_id: int) -> User | None:
    with open_session() as session:
        return session.query(User).filter(User.id == user_id).first()


def get_users() -> list[User]:
    with open_session() as session:
        return session.query(User).all()


def update_user(user: User) -> None:
    with open_session() as session:
        session.merge(user)


def reset_users() -> None:
    with open_session() as session:
        users = session.query(User).all()
        for user in users:
            for guess_data in user.user_guess_data:
                guess_data.guesses = 0
                if not guess_data.answered:
                    guess_data.streak = 0
                guess_data.answered = False
            session.merge(user)
