from database.models import Language, UserGuessData
from database.database import open_session


def get_user_guess_data(user_id: int, language: Language) -> UserGuessData:
    with open_session() as session:
        data = session.query(UserGuessData).filter(
            UserGuessData.user_id == user_id,
            UserGuessData.language == language
        ).first()
        if data is None:
            new_data = UserGuessData(user_id=user_id, language=language)
            session.add(new_data)
            return new_data
        return data


def update_user_guess_data(data: UserGuessData) -> None:
    with open_session() as session:
        session.merge(data)
