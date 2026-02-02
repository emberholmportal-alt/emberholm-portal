"""
Narrative Data for Emberholm Micro-Missions

This module contains all narrative content for the 15 micro-missions:
- 5 EASY missions (10 steps each, 2 min timer)
- 5 MEDIUM missions (20 steps each, 3 min timer)
- 5 HARD missions (35 steps each, 5 min timer)

Each step has:
- text: The narrative description
- choice_a: Cautious option (bold=0)
- choice_b: Bold option (bold=1)

Final ending is calculated based on bold_score / total_steps ratio:
- 80%+ bold = LEGENDARY
- 60%+ bold = PERFECT
- 40%+ bold = GOOD
- <40% bold = NEUTRAL
"""

# Standard endings used by all missions
STANDARD_ENDINGS = {
    "END_LEGENDARY": {
        "type": "LEGENDARY",
        "text": "Legendary success! Your bold choices have forged a path of glory through Emberholm.",
        "xp_mod": 2.0,
        "ember_mod": 2.0
    },
    "END_PERFECT": {
        "type": "PERFECT",
        "text": "Excellent work! Your balanced approach has yielded exceptional results.",
        "xp_mod": 1.5,
        "ember_mod": 1.5
    },
    "END_GOOD": {
        "type": "GOOD",
        "text": "Well done! The mission concludes successfully.",
        "xp_mod": 1.2,
        "ember_mod": 1.2
    },
    "END_NEUTRAL": {
        "type": "NEUTRAL",
        "text": "The mission is complete, though a bolder approach might have yielded greater rewards.",
        "xp_mod": 1.0,
        "ember_mod": 1.0
    }
}


def generate_linear_narrative(steps_content):
    """
    Generate a linear narrative structure with scoring-based endings.

    Args:
        steps_content: List of dicts with 'text', 'choice_a', 'choice_b'

    Returns:
        Dict with steps, endings, total_steps, and scoring flag
    """
    total_steps = len(steps_content)
    steps = {}

    for i, step in enumerate(steps_content):
        step_num = i + 1
        is_last = (step_num == total_steps)

        if is_last:
            steps[str(step_num)] = {
                "text": step['text'],
                "choices": [
                    {"id": "A", "text": step.get('choice_a', 'Conclude carefully'), "next": "CALC_END", "bold": 0},
                    {"id": "B", "text": step.get('choice_b', 'Finish with flair'), "next": "CALC_END", "bold": 1}
                ]
            }
        else:
            steps[str(step_num)] = {
                "text": step['text'],
                "choices": [
                    {"id": "A", "text": step.get('choice_a', 'Be cautious'), "next": str(step_num + 1), "bold": 0},
                    {"id": "B", "text": step.get('choice_b', 'Be bold'), "next": str(step_num + 1), "bold": 1}
                ]
            }

    return {
        "steps": steps,
        "endings": STANDARD_ENDINGS,
        "total_steps": total_steps,
        "scoring": True
    }


# =============================================================================
# EASY MISSIONS (10 steps each)
# =============================================================================

MM_E001_STEPS = [
    {"text": "The ancient brazier burns with an otherworldly flame. Whispers echo from its depths, speaking in a language older than the Portal itself.", "choice_a": "Listen quietly from a distance", "choice_b": "Step closer to hear clearly"},
    {"text": "The whispers grow clearer, speaking of the First Flame's origins. The heat intensifies around you.", "choice_a": "Shield yourself with a ward", "choice_b": "Embrace the warmth fully"},
    {"text": "Visions begin to form in the flames - scenes of Emberholm's founding. A figure beckons you forward.", "choice_a": "Observe the visions carefully", "choice_b": "Reach toward the figure"},
    {"text": "The spectral figure reveals itself as a Flame Guardian. It offers to share ancient knowledge.", "choice_a": "Ask about defensive techniques", "choice_b": "Request forbidden secrets"},
    {"text": "The Guardian speaks of a trial - to prove your worth to the First Flame.", "choice_a": "Accept humbly and prepare", "choice_b": "Declare your readiness boldly"},
    {"text": "Flames swirl around you, testing your resolve. The heat becomes almost unbearable.", "choice_a": "Endure patiently", "choice_b": "Channel the heat into power"},
    {"text": "You pass through the flames and emerge transformed. New understanding fills your mind.", "choice_a": "Absorb the knowledge slowly", "choice_b": "Demand more revelations"},
    {"text": "The Guardian offers a final gift - a spark of the First Flame itself.", "choice_a": "Accept graciously", "choice_b": "Ask how to amplify its power"},
    {"text": "The spark bonds with your essence. You feel its ancient power coursing through you.", "choice_a": "Let it settle naturally", "choice_b": "Push to unlock its full potential"},
    {"text": "The ritual concludes. The Whispering Flame has marked you as one of its chosen.", "choice_a": "Bow in gratitude and depart", "choice_b": "Proclaim your new status proudly"}
]

MM_E002_STEPS = [
    {"text": "Glowing embers dot the Ashen Fields, fading slowly into the void. You must gather them before they disappear.", "choice_a": "Collect methodically nearby", "choice_b": "Rush to the brightest clusters"},
    {"text": "Your hands fill with warm embers. A trail of brighter ones leads deeper into the fields.", "choice_a": "Secure what you have first", "choice_b": "Follow the bright trail"},
    {"text": "The trail leads to a small crater where embers congregate. Something stirs in the shadows nearby.", "choice_a": "Gather quietly and watch", "choice_b": "Investigate the shadow"},
    {"text": "A spirit guardian emerges - protector of the ember fields. It watches you with ancient eyes.", "choice_a": "Show respect and explain your purpose", "choice_b": "Stand your ground confidently"},
    {"text": "The guardian speaks of a mother ember hidden deeper. It could grant you far greater rewards.", "choice_a": "Thank it and continue gathering here", "choice_b": "Ask it to guide you there"},
    {"text": "You venture deeper. The embers here pulse with stronger energy, almost alive.", "choice_a": "Collect carefully, one at a time", "choice_b": "Gather in large handfuls"},
    {"text": "A tremor shakes the ground. The mother ember's location is revealed - but the path is treacherous.", "choice_a": "Take the safer longer route", "choice_b": "Cross directly through the unstable ground"},
    {"text": "You reach the mother ember's chamber. Its radiance is almost blinding.", "choice_a": "Take only a small fragment", "choice_b": "Attempt to claim a large piece"},
    {"text": "The mother ember responds to your presence, offering more of itself freely.", "choice_a": "Accept what it offers", "choice_b": "Request even more"},
    {"text": "Your gathering complete, the spirit guardian appears one last time to bless your haul.", "choice_a": "Accept the blessing quietly", "choice_b": "Ask for additional guidance"}
]

MM_E003_STEPS = [
    {"text": "You take your position at the Portal's edge. Strange mists swirl with unknown dangers.", "choice_a": "Maintain position and observe", "choice_b": "Venture into the mists"},
    {"text": "A disturbance ripples through the veil - something approaches from beyond.", "choice_a": "Signal for backup", "choice_b": "Prepare to face it alone"},
    {"text": "A void scout emerges, testing the barrier's strength. It hasn't noticed you yet.", "choice_a": "Track its movements silently", "choice_b": "Confront it immediately"},
    {"text": "The scout begins probing for weaknesses in the Portal's defenses.", "choice_a": "Document its methods", "choice_b": "Interrupt its work"},
    {"text": "You engage the scout. It's fast and cunning, but you have the advantage of position.", "choice_a": "Fight defensively", "choice_b": "Attack aggressively"},
    {"text": "The scout retreats toward a tear forming in reality. Others may follow.", "choice_a": "Let it go and seal the tear", "choice_b": "Pursue and eliminate it"},
    {"text": "You reach the tear. Void energy pours through, corrupting the surrounding area.", "choice_a": "Begin careful sealing rituals", "choice_b": "Force it closed with raw power"},
    {"text": "The seal holds, but more movement stirs beyond the veil.", "choice_a": "Strengthen the seal and retreat", "choice_b": "Stand guard for further threats"},
    {"text": "A final scout attempts to breach. This one is larger, more dangerous.", "choice_a": "Call for reinforcements", "choice_b": "Face it yourself"},
    {"text": "The perimeter is secure. Your patrol has prevented a potential invasion.", "choice_a": "File a detailed report", "choice_b": "Request assignment to the front lines"}
]

MM_E004_STEPS = [
    {"text": "The ancient rune stone hums with power older than memory. Your mind begins to resonate with its energy.", "choice_a": "Empty your mind completely", "choice_b": "Focus your will upon it"},
    {"text": "Symbols dance at the edge of your vision - fragments of runic knowledge.", "choice_a": "Let them flow through you", "choice_b": "Try to grasp and hold them"},
    {"text": "A presence stirs within the stone - one of the First Runesmiths, preserved in essence.", "choice_a": "Wait for it to speak", "choice_b": "Demand its attention"},
    {"text": "The Runesmith acknowledges your meditation. It offers to test your understanding.", "choice_a": "Accept the basic test", "choice_b": "Request the advanced trial"},
    {"text": "Runes flash before you in rapid succession. You must identify their meanings.", "choice_a": "Answer only what you're sure of", "choice_b": "Trust your instincts on all"},
    {"text": "The test intensifies. Now you must combine runes into working patterns.", "choice_a": "Use established combinations", "choice_b": "Experiment with new forms"},
    {"text": "Your experimental rune creates an unexpected effect - the Runesmith is intrigued.", "choice_a": "Explain your reasoning humbly", "choice_b": "Claim it was intentional mastery"},
    {"text": "The Runesmith offers to share a lost rune - one erased from common knowledge.", "choice_a": "Accept with proper reverence", "choice_b": "Ask why it was erased"},
    {"text": "The forbidden rune sears into your memory. Its power is immense but dangerous.", "choice_a": "Seal it away for study later", "choice_b": "Begin practicing it immediately"},
    {"text": "The meditation concludes. The rune stone falls silent, but you are forever changed.", "choice_a": "Leave a offering of thanks", "choice_b": "Mark the stone as your own"}
]

MM_E005_STEPS = [
    {"text": "The heat of the Eternal Forge washes over you. The master smith measures you with ancient eyes.", "choice_a": "Offer to work the bellows", "choice_b": "Ask to observe his technique"},
    {"text": "The master begins his work. Each hammer strike rings with purpose and power.", "choice_a": "Watch and learn silently", "choice_b": "Ask questions about his methods"},
    {"text": "He pauses and gestures for you to try. A piece of raw metal awaits on the anvil.", "choice_a": "Follow his technique exactly", "choice_b": "Add your own style to the work"},
    {"text": "The metal responds to your strikes. The master nods - you show promise.", "choice_a": "Continue the basic work", "choice_b": "Attempt a more complex shape"},
    {"text": "Your piece takes form. Now it must be tempered in the sacred flames.", "choice_a": "Let the master handle tempering", "choice_b": "Insist on doing it yourself"},
    {"text": "The tempering reveals flaws in the metal. Quick action is needed.", "choice_a": "Start over with new metal", "choice_b": "Attempt to salvage the piece"},
    {"text": "Your improvisation works - the flaw becomes a feature. The master is impressed.", "choice_a": "Credit luck and his teaching", "choice_b": "Accept praise for your skill"},
    {"text": "The final shaping begins. This will determine the piece's ultimate form.", "choice_a": "Create something practical", "choice_b": "Aim for something exceptional"},
    {"text": "The master offers to add his mark alongside yours - a rare honor.", "choice_a": "Accept humbly", "choice_b": "Ask to add the Guild's mark too"},
    {"text": "Your time at the forge ends. The piece you created will serve Emberholm well.", "choice_a": "Gift it to the Guild", "choice_b": "Keep it as your own"}
]


# =============================================================================
# MEDIUM MISSIONS (20 steps each)
# =============================================================================

MM_M001_STEPS = [
    {"text": "Strange sounds emanate from a tear in reality. The void whispers secrets that mortal ears were never meant to hear.", "choice_a": "Cast protective wards first", "choice_b": "Move closer immediately"},
    {"text": "The whispers grow louder - they speak of ancient times before the Portal existed.", "choice_a": "Document what you hear", "choice_b": "Try to communicate back"},
    {"text": "A response comes from the void - something intelligent acknowledges your presence.", "choice_a": "Proceed with extreme caution", "choice_b": "Establish direct contact"},
    {"text": "The void entity reveals itself partially - a being of pure darkness and starlight.", "choice_a": "Maintain your distance", "choice_b": "Approach for closer study"},
    {"text": "It speaks of the time before creation, when only the void existed.", "choice_a": "Listen and record everything", "choice_b": "Ask probing questions"},
    {"text": "The entity offers to show you visions of the primordial void.", "choice_a": "Decline politely", "choice_b": "Accept the offer"},
    {"text": "Visions flood your mind - the birth of the First Flame, the creation of the Portal.", "choice_a": "Focus on retaining details", "choice_b": "Push deeper into the visions"},
    {"text": "You see Emberholm's founding - but the truth differs from the legends.", "choice_a": "Accept this new knowledge", "choice_b": "Demand to see more"},
    {"text": "The entity warns that too much truth can shatter a mortal mind.", "choice_a": "Heed the warning", "choice_b": "Insist you can handle it"},
    {"text": "A final revelation awaits - the true nature of the void itself.", "choice_a": "Decline this knowledge", "choice_b": "Accept whatever comes"},
    {"text": "The void is not empty - it is full of potential, waiting to become.", "choice_a": "Contemplate this wisdom", "choice_b": "Ask how to harness this potential"},
    {"text": "The entity offers a gift - a fragment of void essence.", "choice_a": "Refuse the dangerous gift", "choice_b": "Accept it carefully"},
    {"text": "The essence bonds with you, granting new perception of reality's edges.", "choice_a": "Contain its influence", "choice_b": "Let it expand your senses"},
    {"text": "You can now see tears in reality before they fully form.", "choice_a": "Use this for defense only", "choice_b": "Explore its offensive potential"},
    {"text": "The entity begins to withdraw back into the void.", "choice_a": "Let it go peacefully", "choice_b": "Ask it to stay longer"},
    {"text": "Before leaving, it marks you as a friend of the void - a rare honor.", "choice_a": "Accept the mark humbly", "choice_b": "Ask what privileges it grants"},
    {"text": "Other void beings will now recognize you as an ally.", "choice_a": "Hope to never need this", "choice_b": "Plan to use this advantage"},
    {"text": "The tear begins to seal naturally. Your investigation nears its end.", "choice_a": "Help seal it completely", "choice_b": "Keep it slightly open for future contact"},
    {"text": "You compile your findings - knowledge that could change Emberholm forever.", "choice_a": "Report everything officially", "choice_b": "Keep some secrets for yourself"},
    {"text": "The void echoes fade, but their whispers will stay with you always.", "choice_a": "Return to normal duties", "choice_b": "Seek out more void phenomena"}
]

MM_M002_STEPS = [
    {"text": "The Guild Hall buzzes with tension. A theft has occurred - sacred artifacts are missing.", "choice_a": "Begin systematic investigation", "choice_b": "Trust your instincts on suspects"},
    {"text": "Witnesses report seeing a cloaked figure near the vault last night.", "choice_a": "Interview all witnesses thoroughly", "choice_b": "Search for the cloaked figure directly"},
    {"text": "A trail of faint magical residue leads from the vault toward the lower quarters.", "choice_a": "Follow it carefully", "choice_b": "Rush ahead to catch the thief"},
    {"text": "The trail splits - one path leads to the markets, another to the old tunnels.", "choice_a": "Take the market path", "choice_b": "Explore the dangerous tunnels"},
    {"text": "In the tunnels, you find signs of recent passage and discarded wrappings.", "choice_a": "Collect evidence methodically", "choice_b": "Press forward quickly"},
    {"text": "Voices echo ahead - the thieves are near and seem to be arguing.", "choice_a": "Listen to gather intelligence", "choice_b": "Confront them now"},
    {"text": "There are three of them - more than expected. They're dividing the stolen goods.", "choice_a": "Wait for backup", "choice_b": "Attack while they're distracted"},
    {"text": "Your ambush catches them off guard. Two flee while one stands to fight.", "choice_a": "Subdue this one for questioning", "choice_b": "Pursue the fleeing thieves"},
    {"text": "The captured thief reveals they're part of a larger network.", "choice_a": "Secure prisoner and report", "choice_b": "Demand the network's location"},
    {"text": "Under pressure, they reveal a hideout in the Merchant Quarter.", "choice_a": "Coordinate with Guild forces", "choice_b": "Raid the hideout alone"},
    {"text": "The hideout is a front for a black market operation dealing in stolen relics.", "choice_a": "Observe and document", "choice_b": "Infiltrate the operation"},
    {"text": "Inside, you recognize some of the stolen artifacts among many others.", "choice_a": "Focus on recovering Guild property", "choice_b": "Try to shut down the whole operation"},
    {"text": "The operation's leader notices your presence - a former Guild member turned rogue.", "choice_a": "Attempt to reason with them", "choice_b": "Prepare for confrontation"},
    {"text": "They offer a deal - the artifacts for your silence about their operation.", "choice_a": "Pretend to accept, then betray them", "choice_b": "Refuse outright and fight"},
    {"text": "Combat erupts. The rogue is skilled but your training proves superior.", "choice_a": "Fight defensively to wear them down", "choice_b": "Go all out for quick victory"},
    {"text": "The rogue falls, and their operation crumbles. Stolen goods are everywhere.", "choice_a": "Secure everything for the Guild", "choice_b": "Claim a finder's fee first"},
    {"text": "Among the recovered items, you find artifacts of immense power.", "choice_a": "Report them all immediately", "choice_b": "Examine them privately first"},
    {"text": "One artifact responds to your touch - it seems to choose you.", "choice_a": "Resist its call", "choice_b": "Accept the bond it offers"},
    {"text": "Guild reinforcements arrive to secure the scene and prisoners.", "choice_a": "Give full credit to your team", "choice_b": "Accept recognition as the hero"},
    {"text": "The investigation concludes with the network dismantled and artifacts recovered.", "choice_a": "Request a quiet commendation", "choice_b": "Accept public celebration"}
]

MM_M003_STEPS = [
    {"text": "Void beast tracks scar the scorched earth. These creatures grow bolder each day.", "choice_a": "Study the tracks carefully", "choice_b": "Follow them immediately"},
    {"text": "The tracks lead toward the Boundary Wastes - territory rarely patrolled.", "choice_a": "Request additional support", "choice_b": "Continue alone"},
    {"text": "Fresh droppings indicate the pack is nearby. The hunt has truly begun.", "choice_a": "Set up an observation point", "choice_b": "Move to intercept"},
    {"text": "You spot the pack - six void beasts feeding on corrupted plants.", "choice_a": "Count and document their numbers", "choice_b": "Look for the alpha"},
    {"text": "The alpha is massive, scarred from many battles. It senses something is wrong.", "choice_a": "Remain perfectly still", "choice_b": "Prepare for discovery"},
    {"text": "A younger beast wanders close to your position, sniffing the air.", "choice_a": "Hold your breath and wait", "choice_b": "Eliminate it silently"},
    {"text": "The pack moves on, heading deeper into the wastes. You must decide.", "choice_a": "Trail them from safe distance", "choice_b": "Get ahead to set an ambush"},
    {"text": "You find their den - a corrupted cave pulsing with void energy.", "choice_a": "Map the location and retreat", "choice_b": "Investigate the den"},
    {"text": "Inside, void beast pups huddle together. The pack uses this as a nursery.", "choice_a": "Leave the pups alone", "choice_b": "Eliminate the threat at its source"},
    {"text": "The alpha returns unexpectedly. You're trapped between it and the den.", "choice_a": "Find a hiding spot", "choice_b": "Face the alpha directly"},
    {"text": "The confrontation is inevitable. The alpha charges with terrifying speed.", "choice_a": "Dodge and counterattack", "choice_b": "Meet its charge head-on"},
    {"text": "Your blade finds its mark, but the alpha fights on. The pack converges.", "choice_a": "Focus on defense", "choice_b": "Press your attack on the alpha"},
    {"text": "The alpha falls. The pack hesitates, their leader gone.", "choice_a": "Use the moment to escape", "choice_b": "Establish dominance over the pack"},
    {"text": "Amazingly, the pack submits to you. Your victory has made you their new alpha.", "choice_a": "Drive them away from settled lands", "choice_b": "Consider their potential as allies"},
    {"text": "The void beasts could serve Emberholm's defense if properly directed.", "choice_a": "Report this discovery officially", "choice_b": "Keep your new pack secret"},
    {"text": "You lead the pack on a patrol, testing their obedience.", "choice_a": "Give simple, safe commands", "choice_b": "Test their combat capabilities"},
    {"text": "The pack responds well to your leadership. A new possibility emerges.", "choice_a": "Train them for defensive patrols", "choice_b": "Prepare them for offensive operations"},
    {"text": "Word of your accomplishment reaches the Guild. They're both impressed and concerned.", "choice_a": "Offer to surrender the pack", "choice_b": "Argue for keeping them"},
    {"text": "A compromise is reached - you'll lead a new Void Beast Handler unit.", "choice_a": "Accept with humility", "choice_b": "Demand proper resources"},
    {"text": "Your tracking mission has evolved into something far greater than expected.", "choice_a": "Focus on the responsibility", "choice_b": "Embrace the glory"}
]

MM_M004_STEPS = [
    {"text": "The Singing Caves resonate with crystalline harmonies. Each step releases new notes from the formations.", "choice_a": "Move slowly and listen", "choice_b": "Press deeper quickly"},
    {"text": "The crystals respond to your presence, their song shifting as you pass.", "choice_a": "Try to harmonize with them", "choice_b": "Ignore the music and focus"},
    {"text": "A chamber opens before you, filled with crystals of stunning variety.", "choice_a": "Harvest the common ones first", "choice_b": "Seek out the rarest specimens"},
    {"text": "You find a vein of pure resonance crystal - extremely valuable.", "choice_a": "Extract carefully to preserve quality", "choice_b": "Take as much as possible"},
    {"text": "The cave song changes to a warning tone. Something doesn't like your harvesting.", "choice_a": "Stop and assess the threat", "choice_b": "Continue harvesting quickly"},
    {"text": "A crystal guardian materializes - an elemental being of pure resonance.", "choice_a": "Attempt to communicate", "choice_b": "Prepare to defend yourself"},
    {"text": "The guardian demands to know your purpose in its domain.", "choice_a": "Explain the Guild's needs humbly", "choice_b": "Assert your right to harvest"},
    {"text": "It offers a deal - serve the caves' interests, and harvest freely.", "choice_a": "Accept the bargain", "choice_b": "Negotiate for better terms"},
    {"text": "The guardian asks you to cleanse a corrupted section of the caves.", "choice_a": "Agree to help willingly", "choice_b": "Demand payment upfront"},
    {"text": "The corruption stems from void energy seeping through a crack in reality.", "choice_a": "Seal it with standard methods", "choice_b": "Use the crystals' resonance to seal it"},
    {"text": "Your innovative approach works - the crystals sing the crack closed.", "choice_a": "Thank the caves for their aid", "choice_b": "Claim credit for the technique"},
    {"text": "The guardian is impressed. It reveals the location of the Mother Crystal.", "choice_a": "Express gratitude and follow", "choice_b": "Ask what you can take from it"},
    {"text": "The Mother Crystal is enormous, the source of all resonance in these depths.", "choice_a": "Observe with reverence", "choice_b": "Request permission to harvest"},
    {"text": "The guardian allows you to take a single fragment - choose wisely.", "choice_a": "Take a small, perfect piece", "choice_b": "Take the largest piece possible"},
    {"text": "The fragment pulses with incredible power in your hands.", "choice_a": "Contain its energy carefully", "choice_b": "Let its power flow through you"},
    {"text": "The caves gift you additional crystals as thanks for your service.", "choice_a": "Accept only what you need", "choice_b": "Take everything offered"},
    {"text": "The guardian offers to teach you the secret language of crystals.", "choice_a": "Learn the basics only", "choice_b": "Absorb all the knowledge offered"},
    {"text": "With your new knowledge, you can sense crystals throughout Emberholm.", "choice_a": "Use this gift responsibly", "choice_b": "Plan to exploit every vein"},
    {"text": "Your haul is exceptional - the finest crystals harvested in generations.", "choice_a": "Share credit with the caves", "choice_b": "Present it as your skill alone"},
    {"text": "The Singing Caves bid you farewell, their song now including your name.", "choice_a": "Promise to return respectfully", "choice_b": "Mark the location for future exploitation"}
]

MM_M005_STEPS = [
    {"text": "The veil between worlds grows thin. Ghostly shapes of fallen emissaries shimmer before you.", "choice_a": "Kneel in respect and wait", "choice_b": "Call out to them directly"},
    {"text": "The spirits acknowledge your presence. An ancient warrior steps forward.", "choice_a": "Ask permission to speak", "choice_b": "State your purpose boldly"},
    {"text": "The warrior speaks of battles in the old wars against the Void.", "choice_a": "Listen with humility", "choice_b": "Ask tactical questions"},
    {"text": "Other spirits gather - scholars, healers, craftsmen of ages past.", "choice_a": "Learn from each in turn", "choice_b": "Seek out the most powerful"},
    {"text": "A scholar spirit offers knowledge lost to the living world.", "choice_a": "Request only what is safe", "choice_b": "Ask for forbidden lore"},
    {"text": "The forbidden knowledge concerns the Portal's true nature.", "choice_a": "Accept only hints", "choice_b": "Demand complete understanding"},
    {"text": "The Portal was not created - it was awakened. Something sleeps within.", "choice_a": "Be satisfied with this revelation", "choice_b": "Press for more about what sleeps"},
    {"text": "The spirits grow uneasy discussing this topic. Ancient oaths bind them.", "choice_a": "Respect their silence", "choice_b": "Find ways around the oaths"},
    {"text": "A healer spirit offers to mend old wounds in your soul you didn't know existed.", "choice_a": "Accept gentle healing", "choice_b": "Request complete restoration"},
    {"text": "The healing reveals memories from past lives - you have walked Emberholm before.", "choice_a": "Accept this knowledge quietly", "choice_b": "Explore your past incarnations"},
    {"text": "Your previous self was a hero of the old wars, fallen in glorious battle.", "choice_a": "Honor their sacrifice", "choice_b": "Reclaim their power"},
    {"text": "The warrior spirit recognizes you as their old comrade, reborn.", "choice_a": "Acknowledge the connection humbly", "choice_b": "Embrace your legendary past"},
    {"text": "They offer to restore your old abilities through spirit communion.", "choice_a": "Accept partial restoration", "choice_b": "Demand full awakening"},
    {"text": "Power flows through you - techniques from another age become yours again.", "choice_a": "Practice them carefully", "choice_b": "Test their full potential"},
    {"text": "The spirits warn that drawing too much from them weakens the veil.", "choice_a": "Cease taking immediately", "choice_b": "Take just a little more"},
    {"text": "A disturbance ripples through the spirit realm - something dark approaches.", "choice_a": "Prepare defensive measures", "choice_b": "Confront it directly"},
    {"text": "A void wraith has sensed the thinning veil and seeks to break through.", "choice_a": "Seal the veil and banish it", "choice_b": "Destroy it in spirit combat"},
    {"text": "Using your restored abilities, you defeat the wraith. The spirits are grateful.", "choice_a": "Dismiss their thanks humbly", "choice_b": "Accept their eternal gratitude"},
    {"text": "They bestow a final blessing - the ability to call upon them in dire need.", "choice_a": "Accept this gift solemnly", "choice_b": "Ask how often you can call them"},
    {"text": "The communion ends. You return to the mortal world forever changed.", "choice_a": "Keep these experiences private", "choice_b": "Share this knowledge widely"}
]


# =============================================================================
# HARD MISSIONS (35 steps each)
# =============================================================================

MM_H001_STEPS = [
    {"text": "A tear in reality screams before you. Void energy pours through, corrupting everything it touches.", "choice_a": "Begin standard sealing protocols", "choice_b": "Study the rift's unique properties"},
    {"text": "The rift is unusual - it pulses with a rhythm, almost like a heartbeat.", "choice_a": "Ignore the anomaly and seal it", "choice_b": "Investigate the pulsing pattern"},
    {"text": "The pattern suggests intelligence on the other side, coordinating the breach.", "choice_a": "Increase sealing urgency", "choice_b": "Attempt communication"},
    {"text": "A response comes - not hostile, but curious. Something wants to talk.", "choice_a": "Maintain defensive posture", "choice_b": "Open dialogue cautiously"},
    {"text": "The entity introduces itself as a Void Architect - one who shapes the darkness.", "choice_a": "Demand it close the rift", "choice_b": "Ask about its purpose"},
    {"text": "It claims the rift was accidental, created while building something in the void.", "choice_a": "Offer to help close it properly", "choice_b": "Ask what it was building"},
    {"text": "The Architect was constructing a bridge between realms - for peaceful exchange.", "choice_a": "Reject this as deception", "choice_b": "Consider the possibility"},
    {"text": "It offers proof of peaceful intent - it will withdraw its workers from the rift.", "choice_a": "Wait for proof before acting", "choice_b": "Begin sealing regardless"},
    {"text": "Void workers retreat from the breach. The Architect keeps its word.", "choice_a": "Seal the rift now", "choice_b": "Negotiate further"},
    {"text": "The Architect proposes a controlled connection - beneficial to both realms.", "choice_a": "Refuse any permanent connection", "choice_b": "Hear its full proposal"},
    {"text": "Trade between realms could bring resources Emberholm desperately needs.", "choice_a": "This is beyond your authority", "choice_b": "Express interest in the deal"},
    {"text": "The Architect offers a small demonstration - a gift of void-forged metal.", "choice_a": "Refuse the gift", "choice_b": "Accept it for analysis"},
    {"text": "The metal is unlike anything in Emberholm - light but impossibly strong.", "choice_a": "Still refuse to negotiate", "choice_b": "Admit interest in more"},
    {"text": "A compromise emerges - a temporary, controlled micro-rift for limited trade.", "choice_a": "This requires higher approval", "choice_b": "Agree in principle"},
    {"text": "You must seal the main rift while preparing for potential future cooperation.", "choice_a": "Seal it completely", "choice_b": "Leave a trace connection"},
    {"text": "The sealing process begins. Void energy resists your runes.", "choice_a": "Use more power", "choice_b": "Adjust your technique"},
    {"text": "The Architect assists from its side, teaching you void-sealing methods.", "choice_a": "Accept minimal help", "choice_b": "Learn everything offered"},
    {"text": "Combined techniques work better than either alone. The rift shrinks.", "choice_a": "Complete the seal quickly", "choice_b": "Perfect the technique first"},
    {"text": "Dark shapes move at the rift's edge - not all void beings want peace.", "choice_a": "Focus on the seal only", "choice_b": "Engage the threats"},
    {"text": "Void predators attack, sensing the closing rift as their last chance to cross.", "choice_a": "Defensive fighting while sealing", "choice_b": "Aggressive elimination"},
    {"text": "The Architect helps defend you, proving its claim of peaceful intent.", "choice_a": "Acknowledge the assistance", "choice_b": "Remain suspicious"},
    {"text": "The predators are driven back. The sealing can continue uninterrupted.", "choice_a": "Rush to completion", "choice_b": "Seal it perfectly"},
    {"text": "As the rift closes, the Architect imparts final knowledge - how to contact it again.", "choice_a": "Accept the information reluctantly", "choice_b": "Memorize it eagerly"},
    {"text": "The seal completes. Reality mends itself where the tear once screamed.", "choice_a": "Verify the seal thoroughly", "choice_b": "Trust your work is done"},
    {"text": "Residual void energy remains - it could be cleansed or harvested.", "choice_a": "Cleanse it all", "choice_b": "Collect some for study"},
    {"text": "The surrounding corruption begins to fade. Life may return here eventually.", "choice_a": "Accelerate the healing", "choice_b": "Let nature take its course"},
    {"text": "You find void-touched artifacts scattered near the rift site.", "choice_a": "Destroy them", "choice_b": "Collect them for research"},
    {"text": "One artifact responds to your touch - a communication device of sorts.", "choice_a": "Disable it", "choice_b": "Keep it secret"},
    {"text": "Your mission is technically complete, but the implications are vast.", "choice_a": "Report only the sealing success", "choice_b": "Report everything including the Architect"},
    {"text": "Guild leadership will need to decide on the Architect's proposal.", "choice_a": "Recommend rejection", "choice_b": "Recommend consideration"},
    {"text": "Your report could change Emberholm's relationship with the void forever.", "choice_a": "Present facts without opinion", "choice_b": "Advocate for what you believe"},
    {"text": "The void-forged metal you kept is examined - its value is immeasurable.", "choice_a": "Surrender it to the Guild", "choice_b": "Negotiate to keep some"},
    {"text": "Debate rages about the Architect's proposal. Your testimony is crucial.", "choice_a": "Speak cautiously", "choice_b": "Share your full experience"},
    {"text": "A decision is reached - limited contact will be attempted, with you as liaison.", "choice_a": "Accept reluctantly", "choice_b": "Accept eagerly"},
    {"text": "Your rift-sealing mission has become the first step in a new era.", "choice_a": "Approach the future carefully", "choice_b": "Embrace the possibilities boldly"}
]

MM_H002_STEPS = [
    {"text": "The Lost Outpost appears through the mists - abandoned for centuries, now stirring with activity.", "choice_a": "Survey from a safe distance", "choice_b": "Approach for closer look"},
    {"text": "Ancient defenses still function, powered by forgotten technology.", "choice_a": "Search for a safe entrance", "choice_b": "Test the defenses directly"},
    {"text": "A side passage offers entry, but it's partially collapsed.", "choice_a": "Clear debris carefully", "choice_b": "Squeeze through as-is"},
    {"text": "Inside, dust covers everything. Footprints in the dust show recent visitors.", "choice_a": "Follow the tracks cautiously", "choice_b": "Explore independently"},
    {"text": "The tracks lead to a sealed door with active runic locks.", "choice_a": "Attempt to decipher the runes", "choice_b": "Force the lock"},
    {"text": "The runes are ancient but recognizable - a Guild security system.", "choice_a": "Use standard Guild override", "choice_b": "Try a personal approach"},
    {"text": "The door opens to reveal an intact armory of legendary weapons.", "choice_a": "Document everything first", "choice_b": "Examine the weapons closely"},
    {"text": "These weapons were forged during the First Void War - priceless artifacts.", "choice_a": "Secure them for transport", "choice_b": "Test one immediately"},
    {"text": "A sound echoes deeper in the outpost. You're not alone here.", "choice_a": "Hide and observe", "choice_b": "Investigate the sound"},
    {"text": "Scavengers have found the outpost too - a rival group seeks its treasures.", "choice_a": "Avoid confrontation", "choice_b": "Assert Guild authority"},
    {"text": "The scavengers outnumber you, but they don't know you're here yet.", "choice_a": "Shadow them for information", "choice_b": "Set an ambush"},
    {"text": "They're searching for something specific - a control room mentioned in legends.", "choice_a": "Let them lead you there", "choice_b": "Race them to find it first"},
    {"text": "You find the control room first. Ancient mechanisms hum with dormant power.", "choice_a": "Study the controls carefully", "choice_b": "Activate everything"},
    {"text": "The outpost's defenses can be restored from here - against all intruders.", "choice_a": "Activate selective defenses", "choice_b": "Full defensive activation"},
    {"text": "Alarms blare. The scavengers know someone else is in control now.", "choice_a": "Lock them out completely", "choice_b": "Offer them a chance to leave"},
    {"text": "They refuse to leave and begin forcing their way toward you.", "choice_a": "Use non-lethal defenses", "choice_b": "Deploy full countermeasures"},
    {"text": "The defenses prove overwhelming. The scavengers retreat from the outpost.", "choice_a": "Let them go", "choice_b": "Pursue and capture them"},
    {"text": "Alone now, you can explore the outpost's deeper secrets.", "choice_a": "Proceed methodically", "choice_b": "Hunt for the greatest treasures"},
    {"text": "A hidden vault contains research from the First Void War - tactical innovations.", "choice_a": "Preserve it for Guild scholars", "choice_b": "Study it yourself first"},
    {"text": "The research includes void-weaponry designs never implemented.", "choice_a": "Seal this knowledge away", "choice_b": "Consider its applications"},
    {"text": "Deeper still, you find a cryo-chamber. Someone - something - sleeps within.", "choice_a": "Leave it undisturbed", "choice_b": "Investigate the chamber"},
    {"text": "The occupant is a First War veteran, preserved in stasis for centuries.", "choice_a": "Maintain their sleep", "choice_b": "Consider waking them"},
    {"text": "Waking them could provide invaluable knowledge - or unknown dangers.", "choice_a": "Report and await orders", "choice_b": "Make the decision yourself"},
    {"text": "You initiate the revival sequence. Ancient systems whir to life.", "choice_a": "Stand back cautiously", "choice_b": "Prepare to greet them"},
    {"text": "The veteran awakens - confused, then alert. They reach for a weapon.", "choice_a": "Show peaceful intent", "choice_b": "Restrain them firmly"},
    {"text": "After tense moments, they understand the situation. Centuries have passed.", "choice_a": "Give them time to process", "choice_b": "Brief them on current events"},
    {"text": "They reveal the outpost's true purpose - a last-resort weapon against the Void.", "choice_a": "Learn about it carefully", "choice_b": "Demand to see it immediately"},
    {"text": "The weapon could win any Void war - but its cost is terrible.", "choice_a": "Keep it secret and sealed", "choice_b": "Report it to leadership"},
    {"text": "The veteran offers to serve Emberholm again, sharing their ancient knowledge.", "choice_a": "Accept them cautiously", "choice_b": "Welcome them fully"},
    {"text": "Together, you catalog the outpost's resources. The value is immeasurable.", "choice_a": "Prioritize defensive items", "choice_b": "Focus on power artifacts"},
    {"text": "The outpost could be restored as an active defensive position.", "choice_a": "Recommend this to the Guild", "choice_b": "Suggest other uses"},
    {"text": "Word of your discovery spreads. You've found one of Emberholm's lost treasures.", "choice_a": "Downplay your role", "choice_b": "Accept recognition"},
    {"text": "The veteran chooses you as their heir to First War secrets.", "choice_a": "Accept the responsibility humbly", "choice_b": "Embrace the honor eagerly"},
    {"text": "Your expedition has changed the balance of power in Emberholm.", "choice_a": "Use this power wisely", "choice_b": "Leverage it for advancement"},
    {"text": "The Lost Outpost is lost no more - and neither are its secrets.", "choice_a": "Guard them carefully", "choice_b": "Share them strategically"}
]

MM_H003_STEPS = [
    {"text": "The First Flame's inner sanctum lies ahead. Few are permitted to enter, fewer still return unchanged.", "choice_a": "Proceed with utmost reverence", "choice_b": "Walk boldly into the light"},
    {"text": "The heat intensifies with each step. Lesser flames bow as you pass.", "choice_a": "Acknowledge them humbly", "choice_b": "Stride past with purpose"},
    {"text": "Guardians of flame block the path. They demand proof of worthiness.", "choice_a": "Present your credentials", "choice_b": "Let your actions speak"},
    {"text": "A trial by fire awaits - literally. You must walk through purifying flames.", "choice_a": "Enter slowly and carefully", "choice_b": "Charge through decisively"},
    {"text": "The flames test your resolve, burning away doubt and fear.", "choice_a": "Endure in silence", "choice_b": "Declare your strength"},
    {"text": "You emerge purified. The path to the inner sanctum opens.", "choice_a": "Enter with proper ceremony", "choice_b": "Enter with eager anticipation"},
    {"text": "The First Flame blazes before you - source of all fire in Emberholm.", "choice_a": "Prostrate yourself before it", "choice_b": "Stand tall and meet its gaze"},
    {"text": "A voice speaks from the flame - ancient, powerful, inhuman.", "choice_a": "Listen in reverent silence", "choice_b": "Speak your purpose clearly"},
    {"text": "The Flame asks why you seek its presence.", "choice_a": "Express desire to serve", "choice_b": "Demand power for Emberholm's defense"},
    {"text": "It probes your memories, examining your life's choices.", "choice_a": "Hide nothing", "choice_b": "Guard your secrets"},
    {"text": "The Flame sees your past lives - all the times your soul has served before.", "choice_a": "Accept this revelation", "choice_b": "Question the implication"},
    {"text": "Your soul is old, older than you knew. It has served the Flame many times.", "choice_a": "Embrace this heritage", "choice_b": "Assert your individual identity"},
    {"text": "The Flame offers to awaken your full potential - all lives' accumulated power.", "choice_a": "Accept partial awakening", "choice_b": "Request complete awakening"},
    {"text": "Power floods through you. Memories of battles, loves, losses across centuries.", "choice_a": "Process them slowly", "choice_b": "Absorb them all at once"},
    {"text": "You now carry the wisdom of a dozen lifetimes. The weight is immense.", "choice_a": "Bear it with humility", "choice_b": "Wield it with pride"},
    {"text": "The Flame grants you a gift - a spark of its own essence.", "choice_a": "Accept it with gratitude", "choice_b": "Ask for more"},
    {"text": "The spark bonds with your soul. You are now forever part of the Flame.", "choice_a": "Accept the bond peacefully", "choice_b": "Test its limits immediately"},
    {"text": "With the bond comes responsibility - you must protect the Flame as it protects Emberholm.", "choice_a": "Swear a solemn oath", "choice_b": "Negotiate the terms"},
    {"text": "The Flame reveals a threat - something stirs in the deep void, something old.", "choice_a": "Ask how to prepare", "choice_b": "Demand to face it now"},
    {"text": "An ancient enemy of the Flame awakens. The last time, it nearly destroyed all.", "choice_a": "Learn from past battles", "choice_b": "Develop new strategies"},
    {"text": "The Flame teaches you techniques lost to current generations.", "choice_a": "Practice them methodically", "choice_b": "Master them immediately"},
    {"text": "You learn to shape fire into weapons of extraordinary power.", "choice_a": "Create defensive tools", "choice_b": "Forge offensive weapons"},
    {"text": "The training intensifies. The Flame pushes you to your limits.", "choice_a": "Know your boundaries", "choice_b": "Push past every limit"},
    {"text": "You collapse from exhaustion. The Flame lets you rest in its warmth.", "choice_a": "Recover fully before continuing", "choice_b": "Resume training immediately"},
    {"text": "A vision comes in your rest - the enemy's approach, closer than expected.", "choice_a": "Report this to the Guild", "choice_b": "Keep it between you and the Flame"},
    {"text": "The Flame bestows a title upon you - Champion of the First Fire.", "choice_a": "Accept humbly", "choice_b": "Ask what it entails"},
    {"text": "Champions lead in times of darkness. Your role in the coming battle is crucial.", "choice_a": "Prepare defensively", "choice_b": "Plan offensive operations"},
    {"text": "Other Champions appear - spirits of past bearers of the title.", "choice_a": "Learn from their experiences", "choice_b": "Assert your own path"},
    {"text": "They share techniques unique to each - an arsenal of flame magic.", "choice_a": "Focus on a few techniques", "choice_b": "Try to learn them all"},
    {"text": "The time comes to leave the sanctum. The outside world awaits.", "choice_a": "Depart reluctantly", "choice_b": "Leave eager for action"},
    {"text": "The Guardians bow as you pass. You are now one of them.", "choice_a": "Acknowledge them as equals", "choice_b": "Accept their deference"},
    {"text": "News of your communion spreads. Some view you with awe, others with suspicion.", "choice_a": "Remain humble and approachable", "choice_b": "Embrace your elevated status"},
    {"text": "The Guild asks you to lead the preparation for the coming threat.", "choice_a": "Accept with reservation", "choice_b": "Accept with determination"},
    {"text": "Your communion has prepared you for what comes next.", "choice_a": "Use your power judiciously", "choice_b": "Unleash your full potential"},
    {"text": "The First Flame burns within you now. Emberholm's fate is in your hands.", "choice_a": "Bear this burden solemnly", "choice_b": "Rise to the challenge gloriously"}
]

MM_H004_STEPS = [
    {"text": "The Void Gate pulses with malevolent energy. An invasion force gathers beyond.", "choice_a": "Assess the enemy strength", "choice_b": "Strike preemptively"},
    {"text": "Thousands of void creatures mass at the gate's threshold.", "choice_a": "Call for reinforcements", "choice_b": "Begin thinning their numbers"},
    {"text": "Your attacks draw attention. A void commander emerges to investigate.", "choice_a": "Retreat and regroup", "choice_b": "Challenge the commander"},
    {"text": "The commander is powerful but arrogant. It underestimates you.", "choice_a": "Exploit its arrogance tactically", "choice_b": "Crush it with overwhelming force"},
    {"text": "The commander falls. The void army pauses in confusion.", "choice_a": "Use the lull to fortify", "choice_b": "Press the attack"},
    {"text": "A greater void lord takes command. This one is far more dangerous.", "choice_a": "Observe its tactics", "choice_b": "Engage immediately"},
    {"text": "The void lord begins a ritual to fully open the gate.", "choice_a": "Disrupt the ritual", "choice_b": "Attack the lord directly"},
    {"text": "Your disruption partially succeeds. The gate wavers but holds.", "choice_a": "Continue disruption efforts", "choice_b": "Focus on elimination"},
    {"text": "Reinforcements arrive from Emberholm. The battle truly begins.", "choice_a": "Coordinate defensive lines", "choice_b": "Lead an assault team"},
    {"text": "Wave after wave of void creatures crash against your defenses.", "choice_a": "Hold the line at all costs", "choice_b": "Counterattack between waves"},
    {"text": "The void lord commits its elite guard to the battle.", "choice_a": "Target their leaders", "choice_b": "Meet them head-on"},
    {"text": "An opening appears - a path to the void lord itself.", "choice_a": "Send a strike team", "choice_b": "Go yourself"},
    {"text": "You fight through to the void lord. Its power is immense.", "choice_a": "Fight defensively, find weaknesses", "choice_b": "All-out assault"},
    {"text": "The void lord wounds you badly. Death seems near.", "choice_a": "Fall back to heal", "choice_b": "Press on regardless"},
    {"text": "In your darkest moment, power surges from within - your past lives aid you.", "choice_a": "Channel the power carefully", "choice_b": "Unleash everything"},
    {"text": "Empowered beyond normal limits, you strike the void lord down.", "choice_a": "Ensure its death", "choice_b": "Make it suffer first"},
    {"text": "The void army falters without leadership. Victory is within reach.", "choice_a": "Drive them back systematically", "choice_b": "Pursue total annihilation"},
    {"text": "The gate begins to destabilize. It must be sealed or it will explode.", "choice_a": "Prioritize sealing", "choice_b": "Finish the enemy first"},
    {"text": "Sealing requires entering the gate itself to close it from within.", "choice_a": "Ask for volunteers", "choice_b": "Go yourself"},
    {"text": "Inside the gate, reality twists. The void is vast and hungry.", "choice_a": "Focus only on sealing", "choice_b": "Explore briefly while here"},
    {"text": "The sealing mechanism is guarded by one final void entity.", "choice_a": "Negotiate passage", "choice_b": "Fight through"},
    {"text": "The entity is ancient, tired of war. It may let you pass.", "choice_a": "Appeal to its weariness", "choice_b": "Demand passage"},
    {"text": "It allows passage but warns: sealing the gate seals you inside.", "choice_a": "Accept this fate", "choice_b": "Find another way"},
    {"text": "There is another way - channeling enough power could seal it from outside.", "choice_a": "Attempt the safer method", "choice_b": "Use the guaranteed method"},
    {"text": "You reach the mechanism. The choice is yours - certain sacrifice or risky alternative.", "choice_a": "Risk the alternative", "choice_b": "Make the sacrifice"},
    {"text": "Your gamble works - power from the First Flame itself aids the sealing.", "choice_a": "Thank the Flame silently", "choice_b": "Claim the victory proudly"},
    {"text": "The gate seals. You're thrown clear by the backlash of energy.", "choice_a": "Recover before moving", "choice_b": "Check the seal immediately"},
    {"text": "The seal holds. The invasion is stopped. Emberholm is saved.", "choice_a": "Help with cleanup", "choice_b": "Collapse from exhaustion"},
    {"text": "The cost was high. Many fell defending the realm.", "choice_a": "Honor the fallen first", "choice_b": "Celebrate the victory"},
    {"text": "You're carried back as a hero. Songs will be sung of this day.", "choice_a": "Deflect praise to others", "choice_b": "Accept the adulation"},
    {"text": "The Guild offers you a seat on the High Council.", "choice_a": "Accept reluctantly", "choice_b": "Accept eagerly"},
    {"text": "Your wounds heal, but scars remain - marks of the battle.", "choice_a": "Hide them from view", "choice_b": "Wear them with pride"},
    {"text": "The void threat is diminished but not ended. More battles will come.", "choice_a": "Prepare quietly", "choice_b": "Announce readiness loudly"},
    {"text": "For now, Emberholm is safe because of your actions.", "choice_a": "Remain vigilant always", "choice_b": "Enjoy this hard-won peace"},
    {"text": "The Void Gate is sealed, and your legend is just beginning.", "choice_a": "Stay humble", "choice_b": "Embrace destiny"}
]

MM_H005_STEPS = [
    {"text": "The Eternal Forge burns with unprecedented intensity. A legendary weapon must be created.", "choice_a": "Consult the master smiths", "choice_b": "Trust your own vision"},
    {"text": "The master smiths gather. Each has theories about the perfect blade.", "choice_a": "Consider all opinions equally", "choice_b": "Advocate for your design"},
    {"text": "Materials must be gathered - void-touched metal, First Flame essence, crystal resonance.", "choice_a": "Delegate the gathering", "choice_b": "Collect them personally"},
    {"text": "You venture into dangerous territories to gather the components yourself.", "choice_a": "Take a safe route", "choice_b": "Risk the faster path"},
    {"text": "Void-touched metal lies in a corrupted mine. Creatures lurk within.", "choice_a": "Clear the mine methodically", "choice_b": "Strike fast and extract"},
    {"text": "The metal resists extraction. It seems almost alive, fighting collection.", "choice_a": "Use gentle coaxing", "choice_b": "Force it to submit"},
    {"text": "First Flame essence must be requested from the Flame itself.", "choice_a": "Petition formally", "choice_b": "Claim it as your right"},
    {"text": "The Flame grants essence but warns of the weapon's potential for good or evil.", "choice_a": "Promise to use it wisely", "choice_b": "Assert your control over it"},
    {"text": "Crystal resonance requires the Singing Caves' cooperation.", "choice_a": "Ask the caves' permission", "choice_b": "Take what you need"},
    {"text": "The caves demand a service in return - cleansing a corrupted section.", "choice_a": "Complete the service first", "choice_b": "Promise to return later"},
    {"text": "All components gathered, the forging can begin.", "choice_a": "Follow traditional methods", "choice_b": "Innovate new techniques"},
    {"text": "The metals resist combining. Different essences fight each other.", "choice_a": "Work slowly to harmonize them", "choice_b": "Force them together with power"},
    {"text": "A breakthrough - the materials begin to bond. The weapon takes shape.", "choice_a": "Let it find its own form", "choice_b": "Impose your vision strictly"},
    {"text": "The weapon demands blood - a sacrifice to complete the bond.", "choice_a": "Offer your own blood", "choice_b": "Refuse blood sacrifice"},
    {"text": "Your blood mingles with the metal. The weapon awakens.", "choice_a": "Establish dominance over it", "choice_b": "Form partnership with it"},
    {"text": "The weapon speaks to your mind. It has opinions about its purpose.", "choice_a": "Listen to its perspective", "choice_b": "Assert your will"},
    {"text": "A harmony emerges. The weapon will serve but expects respect.", "choice_a": "Agree to the terms", "choice_b": "Negotiate better terms"},
    {"text": "The tempering process begins. Fire, void, and resonance must balance.", "choice_a": "Follow precise measurements", "choice_b": "Trust your instincts"},
    {"text": "The balance wavers. One element threatens to dominate.", "choice_a": "Reduce that element", "choice_b": "Enhance the others to match"},
    {"text": "Crisis averted. The weapon achieves perfect balance.", "choice_a": "Proceed to finishing", "choice_b": "Attempt to improve further"},
    {"text": "The finishing touches require runic inscription.", "choice_a": "Use standard combat runes", "choice_b": "Create new runes for it"},
    {"text": "Your new runes enhance the weapon's unique properties.", "choice_a": "Limit the enhancement for safety", "choice_b": "Maximize its potential"},
    {"text": "The weapon is nearly complete. Only the naming remains.", "choice_a": "Give it a humble name", "choice_b": "Name it for legend"},
    {"text": "The weapon accepts its name and identity crystallizes.", "choice_a": "Keep the naming private", "choice_b": "Announce it publicly"},
    {"text": "Testing begins. The weapon performs beyond all expectations.", "choice_a": "Test basic functions only", "choice_b": "Push it to extremes"},
    {"text": "At extreme power, the weapon reveals hidden abilities.", "choice_a": "Catalog them for later", "choice_b": "Explore them immediately"},
    {"text": "One ability concerns you - it can open small void rifts.", "choice_a": "Seal this ability away", "choice_b": "Learn to control it"},
    {"text": "Controlling the rift ability could be invaluable in battle.", "choice_a": "Practice in controlled settings", "choice_b": "Test it in the field"},
    {"text": "The weapon is complete. It's one of the finest ever forged.", "choice_a": "Present it to the Guild", "choice_b": "Keep it for yourself"},
    {"text": "The Guild recognizes the weapon's exceptional nature.", "choice_a": "Accept their judgment on its use", "choice_b": "Argue for personal ownership"},
    {"text": "A compromise - you wield it, but it serves Emberholm's interests.", "choice_a": "Accept gratefully", "choice_b": "Negotiate for more autonomy"},
    {"text": "The weapon becomes part of your legend. Songs mention you together.", "choice_a": "Remain humble about it", "choice_b": "Embrace the fame"},
    {"text": "Other legendary smiths seek to study your techniques.", "choice_a": "Share knowledge freely", "choice_b": "Guard your secrets"},
    {"text": "Your creation has changed Emberholm's defensive capabilities forever.", "choice_a": "Use this power responsibly", "choice_b": "Leverage it for influence"},
    {"text": "The legendary forging is complete. You and the weapon are one.", "choice_a": "Bear this bond with honor", "choice_b": "Revel in your achievement"}
]


# =============================================================================
# MISSION NARRATIVES DICTIONARY
# =============================================================================

def get_all_narratives():
    """
    Returns a dictionary of all mission IDs to their narrative data.
    """
    return {
        # EASY missions (10 steps)
        "MM-E001": generate_linear_narrative(MM_E001_STEPS),
        "MM-E002": generate_linear_narrative(MM_E002_STEPS),
        "MM-E003": generate_linear_narrative(MM_E003_STEPS),
        "MM-E004": generate_linear_narrative(MM_E004_STEPS),
        "MM-E005": generate_linear_narrative(MM_E005_STEPS),

        # MEDIUM missions (20 steps)
        "MM-M001": generate_linear_narrative(MM_M001_STEPS),
        "MM-M002": generate_linear_narrative(MM_M002_STEPS),
        "MM-M003": generate_linear_narrative(MM_M003_STEPS),
        "MM-M004": generate_linear_narrative(MM_M004_STEPS),
        "MM-M005": generate_linear_narrative(MM_M005_STEPS),

        # HARD missions (35 steps)
        "MM-H001": generate_linear_narrative(MM_H001_STEPS),
        "MM-H002": generate_linear_narrative(MM_H002_STEPS),
        "MM-H003": generate_linear_narrative(MM_H003_STEPS),
        "MM-H004": generate_linear_narrative(MM_H004_STEPS),
        "MM-H005": generate_linear_narrative(MM_H005_STEPS),
    }


# Categories for missions
MISSION_CATEGORIES = {
    "MM-E001": "LORE",
    "MM-E002": "PATROL",
    "MM-E003": "PATROL",
    "MM-E004": "LORE",
    "MM-E005": "GUILD",
    "MM-M001": "EXPLORATION",
    "MM-M002": "GUILD",
    "MM-M003": "PATROL",
    "MM-M004": "EXPLORATION",
    "MM-M005": "LORE",
    "MM-H001": "LEGENDARY",
    "MM-H002": "EXPLORATION",
    "MM-H003": "LEGENDARY",
    "MM-H004": "LEGENDARY",
    "MM-H005": "GUILD",
}
