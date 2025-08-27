# tools.py
from typing import Dict

book_summaries_dict: Dict[str, str] = {
    "1984": (
        "\"1984\" by George Orwell portrays a totalitarian society ruled by the Party "
        "and watched by Big Brother. Winston Smith tries to resist lies and historical "
        "revisionism, facing the harsh costs of truth and freedom. Core themes: ideological "
        "manipulation, information control, love as an act of rebellion."
    ),
    "The Hobbit": (
        "Bilbo Baggins joins Thorin and his company of dwarves on a perilous quest to the Lonely "
        "Mountain to reclaim a treasure stolen by Smaug. The journey transforms Bilbo from a comfort-seeking "
        "hobbit into a resourceful hero, celebrating wit, friendship, and courage."
    ),
    "To Kill a Mockingbird": (
        "Through Scout Finch’s eyes, the novel explores racial prejudice in 1930s Alabama. "
        "Atticus Finch defends an innocent Black man, while the children learn about empathy, "
        "justice, and growing up in an imperfect world."
    ),
    "The Catcher in the Rye": (
        "Holden Caulfield leaves school and drifts around New York, confronting the phoniness "
        "of adult life and his own anxieties. A meditation on identity, innocence, and the need "
        "for authenticity."
    ),
    "The Fellowship of the Ring": (
        "Book one of Tolkien’s trilogy: Frodo sets out for Mordor to destroy the One Ring. "
        "With the Fellowship, he faces temptations and danger; the theme of collective sacrifice is central."
    ),
    "Harry Potter and the Sorcerer's Stone": (
        "Harry learns he is a wizard and attends Hogwarts, where friendship with Hermione and Ron and "
        "a first encounter with Voldemort’s shadow shape him. A story of courage and identity."
    ),
    "The Name of the Wind": (
        "Kvothe narrates his life: a childhood with the Edema Ruh, profound loss, years at the University, "
        "and the search for truth about the Chandrian and the power of names. Lyrical prose, rich worldbuilding, "
        "and a focus on knowledge and craft."
    ),
    "The Book Thief": (
        "Liesel, living with her foster parents near Munich, steals books and shares them during the war. "
        "Narrated by Death, the story explores life’s fragility and the enduring power of words."
    ),
    "The Kite Runner": (
        "Amir and Hassan grow up in Kabul; a betrayal marks their paths. After emigrating, Amir seeks "
        "redemption. A novel about friendship, guilt, and the hope of forgiveness."
    ),
    "The Road": (
        "A father and his son traverse the ruins of a post-apocalyptic America. Sparse prose underscores "
        "parental love and civilization’s fragility in the search for a safer place."
    ),
    "Dune": (
        "House Atreides takes control of Arrakis, the spice planet. Betrayal forces Paul into the desert "
        "with the Fremen, where he embraces a messianic destiny. An epic of ecology, politics, and religion."
    ),
    "Pride and Prejudice": (
        "Elizabeth Bennet and Mr. Darcy overcome class prejudice and personal pride. Sparkling dialogue, "
        "social critique, and a classic love story."
    ),
    # ---- New 8 to reach 20 ----
    "Brave New World": (
        "Social stability is engineered through conditioning, castes, and the drug soma. Bernard Marx begins "
        "to question the system, and the arrival of John ('the Savage') exposes the human cost of manufactured happiness. "
        "Themes: conformity, freedom, social control."
    ),
    "The Alchemist": (
        "Santiago follows a recurring dream to the Pyramids and learns from an Alchemist that the greatest treasure "
        "is inner transformation. A parable about pursuing one’s Personal Legend, omens, and courage."
    ),
    "The Great Gatsby": (
        "Jay Gatsby constructs a dazzling identity to reclaim Daisy’s love. Through Nick Carraway’s eyes, "
        "the novel unmasks the illusion of the American Dream and the moral emptiness of the elite. "
        "Themes: ambition, illusion, class."
    ),
    "The Handmaid's Tale": (
        "In Gilead, Offred is a Handmaid forced to bear children for the elite. Memories of her past and "
        "small acts of defiance become sources of hope. Themes: oppression, bodily autonomy, resistance."
    ),
    "Crime and Punishment": (
        "Raskolnikov, a poor student in St. Petersburg, commits a murder justified by ideas about "
        "‘extraordinary’ people. Guilt and his relationship with Sonia lead him toward confession and redemption. "
        "Themes: guilt, morality, atonement."
    ),
    "The Little Prince": (
        "A pilot meets a boy from another planet who teaches him to see with the heart. "
        "A meditation on friendship, love, and responsibility. Themes: innocence, meaning, friendship."
    ),
    "The Hunger Games": (
        "Katniss Everdeen volunteers to save her sister and enters a lethal televised competition. "
        "Her defiance sparks hope against the Capitol. Themes: tyranny, sacrifice, media spectacle."
    ),
    "Fahrenheit 451": (
        "Fireman Montag burns books in a society numbed by screens. A chance encounter prompts him to question, "
        "rebel, and preserve cultural memory. Themes: censorship, conformity, knowledge."
    ),
}

def get_summary_by_title(title: str) -> str:
    """Returns the full summary for an exact title; raises KeyError if missing."""
    key = title.strip()
    if key not in book_summaries_dict:
        raise KeyError(f"Title '{title}' is not available in the local database.")
    return book_summaries_dict[key]
