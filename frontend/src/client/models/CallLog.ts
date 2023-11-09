/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * CallLog(*, call_sid: str, phone_number: str, timestamp: datetime.datetime, participant_study_id: str = 'unknown', rejected: Optional[str] = 'false', previous_rejects: int, history: list[tuple[str, str]], syntax_grade: Optional[list] = [], perplexity_grade: Optional[float] = None, memory_exercise_words: Optional[List[str]] = None, memory_exercise_reply: Optional[str] = None, memory_grade: dict = {}, memory_exercise_reply_2: Optional[str] = None, memory_grade_2: dict = {}, l_reply: Optional[str] = None, l_grade: dict = {}, animal_reply: Optional[str] = None, animal_grade: dict = {}, dysarthria_grade: Optional[float] = None, miscellaneous: dict = {})
 */
export type CallLog = {
    call_sid: string;
    phone_number: string;
    timestamp: string;
    participant_study_id?: string;
    rejected?: string;
    previous_rejects: number;
    history: Array<Array<any>>;
    syntax_grade?: Array<any>;
    perplexity_grade?: number;
    memory_exercise_words?: Array<string>;
    memory_exercise_reply?: string;
    memory_grade?: Record<string, any>;
    memory_exercise_reply_2?: string;
    memory_grade_2?: Record<string, any>;
    l_reply?: string;
    l_grade?: Record<string, any>;
    animal_reply?: string;
    animal_grade?: Record<string, any>;
    dysarthria_grade?: number;
    miscellaneous?: Record<string, any>;
};

