"""
LLM Story Generation Module for D&D World Generator

This module provides functionality for generating D&D stories using
either a local LLM model via Hugging Face Transformers or a rule-based
fallback generator when models are not available.
"""

import re
import random
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch


class RuleBasedStoryGenerator:
    """Fallback rule-based story generator for when LLM is not available."""
    
    def __init__(self):
        self.story_templates = [
            "As {character} ventures forward, {event}. {outcome}",
            "{character} {action} and discovers {discovery}. {consequence}",
            "The air grows {atmosphere} as {character} {movement}. {revelation}",
            "Suddenly, {character} {encounter}. {reaction}",
            "{character} {investigation} when {complication} occurs. {resolution}"
        ]
        
        self.events = [
            "a mysterious mist begins to roll in",
            "the sound of distant drums echoes through the area",
            "strange markings appear on nearby trees",
            "a flock of ravens takes flight overhead",
            "the temperature drops noticeably",
            "shadows seem to move independently",
            "a peculiar scent fills the air"
        ]
        
        self.actions = [
            "carefully examines the surroundings",
            "proceeds with caution",
            "draws their weapon",
            "listens intently for any sounds",
            "searches for clues",
            "moves stealthily forward",
            "pauses to assess the situation"
        ]
        
        self.discoveries = [
            "an ancient stone covered in runes",
            "tracks leading deeper into the unknown",
            "a hidden passage behind some foliage",
            "remnants of a recent campfire",
            "a glint of metal partially buried in the earth",
            "strange symbols carved into the ground",
            "evidence of a struggle that occurred recently"
        ]
        
        self.atmospheres = ["thick and oppressive", "cold and forbidding", "strangely quiet", "electric with tension"]
        self.movements = ["steps forward cautiously", "moves through the shadows", "advances with determination"]
        self.encounters = ["hears footsteps approaching", "spots movement in the distance", "notices they're being watched"]
        
        self.outcomes = [
            "This could be the key to solving the mystery.",
            "The adventure takes an unexpected turn.",
            "Danger seems to lurk around every corner.",
            "New possibilities present themselves.",
            "The stakes have suddenly become much higher."
        ]
    
    def generate_story(self, prompt="", character_context=""):
        """Generate a story using rule-based templates."""
        character = character_context if character_context else "the adventurer"
        
        template = random.choice(self.story_templates)
        
        # Fill in the template
        story = template.format(
            character=character,
            event=random.choice(self.events),
            action=random.choice(self.actions),
            discovery=random.choice(self.discoveries),
            atmosphere=random.choice(self.atmospheres),
            movement=random.choice(self.movements),
            encounter=random.choice(self.encounters),
            outcome=random.choice(self.outcomes),
            consequence=random.choice(self.outcomes),
            revelation=random.choice(self.outcomes),
            reaction=random.choice(self.outcomes),
            complication=random.choice(self.events),
            investigation=random.choice(self.actions),
            resolution=random.choice(self.outcomes)
        )
        
        return story
    
    def generate_encounter(self, character_level=1, environment="forest"):
        """Generate an encounter based on level and environment."""
        encounters = {
            "forest": [
                "A pack of wolves emerges from the underbrush, their eyes gleaming in the dim light.",
                "An ancient treant slowly awakens from its slumber, curious about the intruders.",
                "Bandits have set up an ambush along the forest path ahead.",
                "A wounded deer leads the party toward a hidden grove where something magical awaits."
            ],
            "dungeon": [
                "The sound of shuffling feet echoes from the chamber ahead - undead guardians stir.",
                "A complex trap mechanism activates as pressure plates are triggered.",
                "Goblin voices can be heard arguing over treasure in the next room.",
                "Strange glyphs on the wall begin to glow ominously as magical wards activate."
            ],
            "city": [
                "A pickpocket attempts to lift coin purses in the crowded marketplace.",
                "City guards approach, questioning everyone about a recent theft.",
                "A mysterious figure in a hooded cloak signals from a dark alley.",
                "A public execution draws a crowd, but something seems amiss about the proceedings."
            ]
        }
        
        env_encounters = encounters.get(environment, encounters["forest"])
        base_encounter = random.choice(env_encounters)
        
        if character_level <= 3:
            difficulty = "The situation seems manageable for a novice adventurer."
        elif character_level <= 10:
            difficulty = "This challenge will test the skills of an experienced adventurer."
        else:
            difficulty = "Even a veteran adventurer should approach this situation with caution."
        
        return f"{base_encounter} {difficulty}"
    
    def generate_npc_dialogue(self, npc_type="innkeeper", context=""):
        """Generate NPC dialogue."""
        dialogues = {
            "innkeeper": [
                "Welcome, traveler! A hot meal and a warm bed await those with coin to spend.",
                "Strange things have been happening in these parts lately. I'd be careful if I were you.",
                "You look like you've seen some adventure. Care to share a tale over some ale?",
                "The roads haven't been safe recently. Travelers speak of dark creatures in the woods."
            ],
            "guard": [
                "Halt! State your business in this area.",
                "We've had reports of suspicious activity. Have you seen anything unusual?",
                "Keep your weapons sheathed within the city walls, stranger.",
                "The captain wants to see all newcomers. You'll need to report to the garrison."
            ],
            "merchant": [
                "Fine wares for the discerning adventurer! What might interest you today?",
                "I've got just the thing you need - at a very reasonable price, of course.",
                "Business has been slow with all the troubles in the region lately.",
                "You look like someone who appreciates quality. Let me show you my best items."
            ]
        }
        
        npc_lines = dialogues.get(npc_type, dialogues["innkeeper"])
        return f'"{random.choice(npc_lines)}"'


class StoryGenerator:
    """Handles LLM-based story generation for D&D scenarios with fallback support."""
    
    def __init__(self, model_name="distilgpt2"):
        """
        Initialize the story generator with a local LLM model.
        
        Args:
            model_name (str): Name of the Hugging Face model to use
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.generator = None
        self._initialized = False
        self._llm_available = False
        
        # Initialize fallback generator
        self.fallback_generator = RuleBasedStoryGenerator()
    
    def _initialize_model(self):
        """Lazy initialization of the LLM model with fallback."""
        if self._initialized:
            return
            
        try:
            print(f"Loading {self.model_name} model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            # Add padding token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                return_full_text=False
            )
            
            self._llm_available = True
            print(f"Model {self.model_name} loaded successfully!")
            
        except Exception as e:
            print(f"LLM model not available ({e}). Using rule-based story generator as fallback.")
            self._llm_available = False
        
        self._initialized = True
    
    def generate_story_continuation(self, prompt, character_context="", max_length=150):
        """
        Generate a story continuation based on a prompt and character context.
        
        Args:
            prompt (str): The story prompt or current situation
            character_context (str): Context about the character(s) involved
            max_length (int): Maximum length of generated text
            
        Returns:
            str: Generated story continuation
        """
        self._initialize_model()
        
        if not self._llm_available:
            # Use fallback generator
            return self.fallback_generator.generate_story(prompt, character_context)
        
        # Create a D&D-focused prompt
        full_prompt = self._create_dnd_prompt(prompt, character_context)
        
        try:
            # Generate text
            outputs = self.generator(
                full_prompt,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.8,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            generated_text = outputs[0]['generated_text']
            
            # Clean up the generated text
            cleaned_text = self._clean_generated_text(generated_text)
            
            return cleaned_text
            
        except Exception as e:
            print(f"Error generating story with LLM: {e}")
            # Fall back to rule-based generator
            return self.fallback_generator.generate_story(prompt, character_context)
    
    def _create_dnd_prompt(self, prompt, character_context):
        """Create a D&D-focused prompt for the LLM."""
        context_prefix = ""
        if character_context:
            context_prefix = f"Character: {character_context}\n\n"
        
        dnd_prompt = f"""{context_prefix}In a fantasy D&D adventure:

{prompt}

The story continues:"""
        
        return dnd_prompt
    
    def _clean_generated_text(self, text):
        """Clean and format the generated text."""
        # Remove excessive whitespace and newlines
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Try to end at a complete sentence
        sentences = text.split('.')
        if len(sentences) > 1:
            # Take all complete sentences
            complete_text = '. '.join(sentences[:-1]) + '.'
            return complete_text
        
        return text
    
    def generate_encounter(self, character_level=1, environment="forest"):
        """
        Generate a random encounter based on character level and environment.
        
        Args:
            character_level (int): Level of the character(s)
            environment (str): Type of environment (forest, dungeon, city, etc.)
            
        Returns:
            str: Generated encounter description
        """
        self._initialize_model()
        
        if not self._llm_available:
            return self.fallback_generator.generate_encounter(character_level, environment)
        
        level_descriptor = "novice" if character_level <= 3 else "experienced" if character_level <= 10 else "veteran"
        
        prompt = f"A {level_descriptor} adventurer encounters something in a {environment}."
        
        return self.generate_story_continuation(prompt, max_length=100)
    
    def generate_npc_dialogue(self, npc_type="innkeeper", context=""):
        """
        Generate NPC dialogue for D&D scenarios.
        
        Args:
            npc_type (str): Type of NPC (innkeeper, guard, merchant, etc.)
            context (str): Additional context for the dialogue
            
        Returns:
            str: Generated NPC dialogue
        """
        self._initialize_model()
        
        if not self._llm_available:
            return self.fallback_generator.generate_npc_dialogue(npc_type, context)
        
        prompt = f"A {npc_type} says to the adventurer"
        if context:
            prompt += f" (context: {context})"
        prompt += ":"
        
        dialogue = self.generate_story_continuation(prompt, max_length=80)
        
        # Format as dialogue
        if not dialogue.startswith('"'):
            dialogue = f'"{dialogue}"'
        
        return dialogue


# Global instance
story_generator = StoryGenerator()