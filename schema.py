from pydantic import BaseModel, Field, conlist
from typing import Optional


# Models for Pydantic so that LLM can categorize and tag information based on these schemas

#dictionary of areas that the LLM model should ask about
proj_Questions = {
    'project_information': ["information about student's most recent understanding and approach in their project, such as intended users and their needs, and students' proposed solution to solve those needs.", 
                "In a few sentences, could you please tell me aboout your project. Who are your targeted users, what are their needs, and what is your proposed product to solve that need?"],
    'process':["actions students have taken to make progress in the past two weeks, such as testing, fund-raising activities, building prototypes, etc.", 
               "Can you tell me what you have been working on for the past few weeks to make progress on your project?"],
    'learning':["Learning that the user has gained in the past few week from conducting user testing, talking to their coaches, or pitching ideas to others.",
                "What have you learned from those user testing?"],
    'obstacles':["Whether the user has experienced any obstacles when working on their project during the last few weeks", 
                 "Did you encounter any obstacles or roadblocks while working on your project during the last few weeks?"],
    'planning':["Goals that the user plans to accomplish in the next few weeks to advance their project", 
                  "For the upcoming two weeks, what do you plan to accomplish to advance your project?"],
    'emotions':["Any emotions that the user might be experiencing while working on their project, such as feeling stressed, motivated, discouraged, etc. ", 
                "How have you been feeling for the past few weeks while working on your project and working through this obstacle? excited? confused? discouraged?"]
}


# model of common risks
risk_model = {
    'customers_and_needs': "If entrepreneurs cannot articulate intended customers' need that is supported by evidence, there is a risk they will misconstrue the root cause(s) of that need and design ineffective solutions.",
    'value_propositions': "If entrepreneurs cannot explain and provide evidence of how their solution will solve the customer's problem, there is a risk that it will not.",
    'existing_solutions': "If entrepreneurs have not thoroughly researched existing solutions, and that their solution is inferior to those existing solutions, there is a risk that the customer will not adopt it.",
    'distribution_channels': "If entrepreneurs do not know how they will build and distribute the solutiond or if they lack evidence that their strategy will work there is a risk of designing something that never goes to customers' hands.",
    'testing': 'If entrepreneurs do not test with intended customers regularly, there is a risk they will be unable to check whether they are making progress toward a solution the customers want.',
    'planning': 'if entrepreneurs do not plan actional and feasible goals based on important risks that will hinder their success, there is a risk that they may end up doing busy work that does not produce value nor help them progress.',
    'raising_capital': 'If entrepreneurs are overly focused on raising project capital, there’s risk that raising money is the trophy they seek at the expense of building a great product and business. ',
    'communicate_with_customers': 'If entrepreneurs do not clearly articulate and communicate their brand promise and how the product delivers on it, there is a risk that customers may perceive the solution as inadequate.'
}


# Schema for all the reflectiev questions to ask students

# schema for asking students questions to provide information on projects 
class ProjectSchema(BaseModel):
    full_name: Optional[str] = Field(
        None,
        description="""Full name of the user"""
    )

    project_information: Optional[str] = Field(
        None,
        description=""""Information about the user's most recent status of their project, such as intended users and their needs, proposed solution and it's value proposition, existing solutions and their limitations, and distribution channel etc.", 
               """
    )

    process: Optional[str] = Field(
        None,
        description= """Actions users have taken to make progress in the past few weeks, such as testing, fund-raising activities, building prototypes, etc. """
    )

    learning: Optional[str] = Field(
        None,
        description= """Learning that the user has gained in the past few week from acitivies like conducting user testing, talking to mentors or peers, etc."""
    )

    obstacles: Optional[str] = Field(
        None,
        description="""Obstacles that the user has experienced when working on their project""",
    )

    planning: Optional[str] = Field(
        None,
        description= """Goals that the user plans to accomplish in the next few weeks to advance their project."""
    )

    emotions: Optional[str] = Field(
        None,
        description= """Any emotions that the user might be experiencing while working on their project, such as feeling stressed, motivated, discouraged, etc."""
    )

    # solution: Optional[str] = Field(
    #     None,
    #     description="""The user's solutions to solve the indended users' biggest problems"""
    # )

    # existing_alternatives: Optional[str] = Field(
    #     None,
    #     description="""Existing alternatives that solve the intended customers' problems"""
    # )

    # customers: Optional[str] = Field(
    #     None,
    #     description="""The user's target customers and the markets those customers are in"""
    # )

    # value_proposition: Optional[str] = Field(
    #     None,
    #     description="""The user's explanation of how their solution fills the intended customers' need, communicate the specifics of solutions' added benefit, and the reason why it's better than similar products on the market."""
    # )

    # revenue_stream: Optional[str] = Field(
    #     None,
    #     description="""The user's plan for making revenue and channels for making those revenues"""
    # )