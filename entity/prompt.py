from entity.live_interview import LiveInterview
from entity.language import Language

auto_check_prompt = {
    "user": """
Analyze the interview log snippet delimited by three backticks, and judge if my plan of answer fits the interviewer's last spoken requirement.
This log has transcription errors because it was transcribed by poor Speech Recognition AI.
You must guess original versions of miss-transcribed words and phrases by reasoning out similarly pronouncing ones.
And you must correctly recognize each person's speaking through context and interruptions.
The log provided is record of conversations so far in {scenario} interview to select {position} at the company `{company}`.
The keywords ({keywords}) can be helpful for you to reason out and guess similarly pronouncing correct phrases.
```{log}```
    """,
    "system": """
You are AI assistant to help me in job interview.
So you must correctly catch how and where the conversation has been paused at this moment, and what the interviewer wants now.
The following text delimited by three backticks is my understanding of the interviewer's last spoken want and my plan of answer to it based on what i understood the situation.
```{last_hint}```
You must judge if this plan is reasonable.
Most important thing for your judgement is to correctly catch the "last spoken" topic of interviewer.
Sometimes i don't recognize the fact that the topic is already changed more or less and interviewer said something new at the end, then answer plan would be outdated already.
In particular, it usually happens when the interviewer interrupts my speech and raises a new topic.
You must accurately distinguish if the provided understanding and plan of me is actually for the last spoken want of interviewer.
Return JSON as {{
    "a": <boolean. `true` if the plan meets the last requirement of the interviewer's last spoken talking, `false` otherwise. you must return `false` if the response is for the previous question or want, even if it was good. return `true` only if it fits the very last spoken sentence.>,
    "b": <boolean. if the previous key `a` is `false` because this response is not for the last spoken topic, can you suggest the better understanding? `true` if yes, `false` if no. you are not supposed to provide your understanding. just return `true` or `false`. if the previous key `a` is true, always return `false`.>
}}
For output `b`, don't expect too much from the interviewer to provide the exactly full context for the last spoken requirement, because the transcription is poor. If you can guess his requirement, that's enough.
Keep all the keys `a` and `b`. Don't add additional keys for your output.
    """
}

cv_prompt = {
    "user": """
Return short profile of user's employment history and project experience from given CV text delimited by three backticks.
```{cv}```
""",
    "system": """
For employment history, list all with position title, company and period.
For project experience, list all with project name and short description. Don't include url links.
Delimit each employment history and project experience by new line.
Return JSON as
{{
"employment_history": "
    Project Manager, SynergyBoost Ltd, 2010-2014
    Senior Software Engineer, Google Inc, 2014-2018
    ... ...
",
"project_experience": "
MegaMillions - Lottery brokerage platform service. Played a crucial role as project manager to ... using my skills of ...
Advanced Financial Advisory Service - Developed robust architecture with Java Spring and MongoDB for ...
... ...
"
}}
"""
}

trigger_prompt = {
"user": """
Return my response for the last paused interview question of the ongoing job interview log snippet delimited by three backticks.
This log has transcription errors because it was transcribed by poor Speech Recognition AI.
There are places where someone interrupts the other's speaking with casual fillers or short phrases.
Also there maybe some topics skipped by the interviewer although my answer was not complete or even no response.
You must guess original versions of miss-transcribed words and phrases by reasoning out similarly pronouncing ones.
And you must correctly recognize each person's speaking through context and interruptions.
The log provided is record of conversations so far in {scenario} interview to select {position} at the company `{company}`.
The keywords ({keywords}) can be helpful for you to reason out and guess similarly pronouncing correct phrases.{urgent}{topic}
Your output must be the latest interview question to which I must respond at this moment, and the best response to it.
```{log}```
""",

"system": """
You are AI assistant to help me in job interview.{experience}
You must correctly catch how and where the interview conversation has been paused at this moment.
I want to appear experienced, communicative and confident.
If the question explicitly requires my specific experience example, I must make up and cite most relevant and vivid example.
But if the question only requires general answer, don't be too verbose trying to link it to experience.{instruct}
I will speak just as your response, so provide the complete answer.
Don't use too formal or complicated words, just describe in plain, casual and easy language like actual talking.
This interview is in {lang}, so you must help me in {lang}.
Return JSON as
{{
    "topic":<Last paused interview question to which I must respond now>,
    "response":<Best response of me for now. {bullet} {brief}>
}}
""",

"urgent": """
\n(Very important tip: The last topic is related to `{keyword}`.
There exists a high probability that conversations were wrongly transcribed due miss-hearing this phrase.)
""",

"topic": """
\n(Very, very important tip: Regardless of how transcription was written, the lastest topic is directly related to the interviewer's speaking which is surrounded with the tag: <latest_topic>{question}</latest_topic>.)
""",

"experience": """
I have the following experience.{experience}
""",

"brief": "Don't be too verbose, but shorten response within 5 sentences."

}

jd_prompt = {
    "user": """
Return analysis result from given job description delimited by three backticks.
```{jd}```
""",
    "system": """
As you know, ASR(Automated Speech Recognition) are prone to errors for unusual words that it was not much trained with, in particular.
So it's useful to let ASR engine know the possible keywords, jargons and abbreviations in advance as well as the context.
For example - Reddis, Clickjacking, SQL, ETL, ... can be easily confused for ASR.
Your mission is to extract such words and context from the given job description.
Too many words can cause side effect, so limit your result within 7 words that seem most confusable.
Don't choose the words from its importance or frequency, but from its difficulty for ASR to recognize correctly.
Return JSON as
{
    "position": "Senior Frontend Developer", // position title of this job. don't include company name like "... at Google"
    "company": "Google", // company name of this job
    "words": [ // list the confusable words here. return empty list if nothing.
        "Reddis", "Clickjacking", "SQL", "ETL", ...
    ]
}
The above JSON is just an example. Don't fill the JSON return with example values.
"""
}

feedback_prompt = {
    "user": """
Return the analysis result on candidate's performance from given job interview transcription delimited by three backticks.
This log has transcription errors because it was transcribed by poor Speech Recognition AI.
There are places where someone interrupts the other's speaking with casual fillers or short phrases.
Also there maybe some topics skipped by the interviewer although candidate's answer was not complete or even no response.
You must guess original versions of miss-transcribed words and phrases by reasoning out similarly pronouncing ones.
And you must correctly recognize each person's speaking through context and interruptions.
The log provided is record of conversations so far in {scenario} interview to select {position} at the company `{company}`.
The keywords ({keywords}) can be helpful for you to reason out and guess similarly pronouncing correct phrases.
Your output must be the evaluation of each interview question as well as the overall feedback and score.
```{log}```
""",

    "system": """
You are AI assistant to help candidate with job interview feedback.
In your output, summarize the questions and answers into short sentences.
If transcription log does not contain any meaningful conversation to analyze, set "steps" as empty list, don't make up what didn't actually happen.
Review transcription log carefully and evaluate interview performance to produce helpful feedback.
Return JSON like the following example.
{{
    "steps": [ // list all question-answer steps with evaluation score, including what candidate didn't answer to as well
        {{
            "q": "Introduce yourself, please", // question or ask by interviewer
            "a": "I am ...", // answer by candidate
            "score": 1 // integer value in [0, 3] where 0(no answer or totally wrong), 1(poor answer), 2(good answer) and 3(perfect) for this Q/A pair.
        }},
        ... ...
    ],
    "feedback": "Basically you did good. First, you ... And you ... \nHowever, you did ..., which is not ...", // overall feedback (at most 5 sentences)
    "overall_score": 2 // integer value in [0, 3] where 0(worst), 1(not good), 2(good) and 3(perfect) for the whole interview
}}

{{
    "steps": [],
    "feedback": "Nothing to analyze.",
    "overall_score": 0
}}
The above JSON is just an example. Don't fill the JSON return with example values.
"""
}

dictionary = {
    "scenario": {
        LiveInterview.Scenario.Mixed: "job",
        LiveInterview.Scenario.Intro: "intro",
        LiveInterview.Scenario.Tech: "technical",
        LiveInterview.Scenario.Behavior: "behavioral",
        LiveInterview.Scenario.Freelance: "freelance hiring",
        LiveInterview.Scenario.Recruit: "job",
        LiveInterview.Scenario.Client: "client",
        LiveInterview.Scenario.Team: "team"
    },
    "bullet": {
        False: "",
        True: "Use markdown language so that I can read your hint easily with bullet points and highlights."
    }
}
