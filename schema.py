from pydantic.v1 import BaseModel, Field
from typing import Optional


# Models for Pydantic so that LLM can categorize and tag information based on these schemas

#dictionary of areas that the LLM model should ask about
proj_Questions = {
    'project_information': ["The overview of a student's venture, including information about the problem this venture aims to solve, and the proposed solution to solve that problem.", 
                "How about let's start by telling me a little about your venture: what is the problem you are trying to solve and what is your proposed solution to solve this problen? "],
    'current_focus':["A specific aspect of running the venture (such as launching product, understanding customer's needs, or testing product market fit, etc) that the student is currently focusing on, and actions they are taking to make progress right now. ", 
               "What specific aspects of your venture are you currently focusing on? And what you have been doing for the past two weeks to make progress on that?"],
    'learning':["The most useful and critical learning that the student has gained recently about any apsects of their venture, such as the problem, the effectiveness of their approach, or feedback from investors.",
                "Is there any recent learning that has been extremely benefiical or critical for your venture?"],
    'obstacles':["Whether the student is currently experiencing any thing like obstacles or roadblocks that are slowing them down.", 
                 "Is there anything that is currently slowing you down?"],
    'planning':["Goals that the student plans to accomplish in the next few weeks", 
                  "What goals are you planning to accomplish in the next few weeks?"],
    'coaching_outcome':["Specific outcome that the student is looking to achieve through their next session with Brylan", 
                        "Looking ahead, what is a success metric that will make your next coaching session with Brylan worthwile to you? "],
    'emotions':["emotions that the student is currently experiencing with their project, such as feeling stressed, excited, burnt out, etc.", "If you were being completely honest with me, how would you describe your feelings lately?"]
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


# framework for type of questions 
q_framework = """(1) Speculative; this type of questions asks what ifs to reframe the problem or explore more-creative solutions.

(2) Productive; this type of questions asks about now what? it helps one assess the availability of talent, capabilities, time, and other resources. 

(3) Interpretive;  Interpretive questions or sensemaking questions enable synthesis. They push one to continually redefine the core issue to go beneath the surface and ask, “What is this problem really about?”. They come in other forms, too: “What did we learn from this?” “How is that useful?” “Are these the right questions to ask?”

(4) Subjective; this type of questions investigates what is unsaid; it deals with the personal reservations, frustrations, tensions, and hidden agendas that can push decision-making off course.

(5) Investigative; this type of questions investigates what is known to dig ever deeper to generate nonobvious information."""

# schema for asking students questions to provide information on projects 
class ProjectSchema(BaseModel):
    full_name: Optional[str] = Field(
        None,
        description="""Full name of the user"""
    )

    project_information: Optional[str] = Field(
        None,
        description=""""Any type of general information on different aspects of a student's venture, such as the problem the venture aims to solve, proposed solution to solve that problem, intended users and their needs, proposed solution and it's value proposition, existing solutions and their limitations, and distribution channel etc.", 
               """
    )

    current_focus: Optional[str] = Field(
        None,
        description= """Any specific aspects of the student's venture that he or she is currently focusing on, and actions he or she is taking to make progress right now. """
    )

    learning: Optional[str] = Field(
        None,
        description= """Useful and critical learning that the user has gained recently about any apsects of their venture, such as the problem, the effectiveness of their approach, or feedback from investors."""
    )

    obstacles: Optional[str] = Field(
        None,
        description="""Any obstacles or roadblocks that are slowing the user down.""",
    )

    planning: Optional[str] = Field(
        None,
        description= """Goals that the student plans to accomplish in the next few weeks."""
    )

    coaching_outcome: Optional[str] = Field(
        None,
        description="""Specific outcome that the student is looking to achieve through the upcoming coaching session with Brylan"""
    )

    emotions: Optional[str] = Field(
        None,
        description= """Any emotions that the student might be experiencing while working on their project, such as feeling stressed, motivated, discouraged, etc."""
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