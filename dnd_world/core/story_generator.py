"""
Story Generation System - Moved from story.py
"""

import random
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

class StorySystem:
    """Main story generation interface"""
    
    def __init__(self):
        self.story_generator = StoryGenerator()
    
    def generate_story_continuation(self, prompt, character_context="", max_length=150):
        return self.story_generator.generate_story_continuation(prompt, character_context, max_length)
    
    def generate_encounter(self, character_level=1, environment="forest"):
        return self.story_generator.generate_encounter(character_level, environment)
    
    def generate_npc_dialogue(self, npc_type="innkeeper", context=""):
        return self.story_generator.generate_npc_dialogue(npc_type, context)

class StoryGenerator:
    """Handles LLM-based story generation for D&D scenarios with fallback support."""
    
    def __init__(self, model_name="distilgpt2"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.generator = None
        self._llm_available = False
        self._initialized = False
        
        # Fallback generator
        self.rule_based_generator = RuleBasedStoryGenerator()
    
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
        Generate a story continuation based on the given prompt.
        
        Args:
            prompt (str): The story prompt or beginning
            character_context (str): Information about the character(s)
            max_length (int): Maximum length of generated text
            
        Returns:
            str: Generated story continuation
        """
        self._initialize_model()
        
        if not self._llm_available:
            return self.rule_based_generator.generate_story_continuation(prompt, character_context)
        
        try:
            # Create D&D-focused prompt
            full_prompt = self._create_dnd_prompt(prompt, character_context)
            
            # Generate text using the LLM
            outputs = self.generator(
                full_prompt,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.8,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            generated_text = outputs[0]['generated_text']
            return self._clean_generated_text(generated_text)
            
        except Exception as e:
            print(f"LLM generation failed: {e}. Using fallback.")
            return self.rule_based_generator.generate_story_continuation(prompt, character_context)
    
    def _create_dnd_prompt(self, prompt, character_context):
        """Create a D&D-focused prompt for the LLM."""
        base_prompt = "In a Dungeons & Dragons adventure: "
        
        if character_context:
            base_prompt += f"{character_context} "
        
        base_prompt += prompt
        
        if not prompt.endswith('.') and not prompt.endswith('!') and not prompt.endswith('?'):
            base_prompt += "."
        
        return base_prompt
    
    def _clean_generated_text(self, text):
        """Clean and format the generated text."""
        # Remove any incomplete sentences at the end
        sentences = text.split('.')
        if len(sentences) > 1 and sentences[-1].strip() and len(sentences[-1]) < 20:
            # Remove last incomplete sentence
            text = '.'.join(sentences[:-1]) + '.'
        
        # Clean up common issues
        text = text.replace('\n\n', ' ')
        text = text.replace('\n', ' ')
        text = ' '.join(text.split())  # Normalize whitespace
        
        return text.strip()
    
    def generate_encounter(self, character_level=1, environment="forest"):
        """Generate a random encounter appropriate for the character level."""
        self._initialize_model()
        
        if not self._llm_available:
            return self.rule_based_generator.generate_encounter(character_level, environment)
        
        prompt = f"The party of level {character_level} adventurers encounters"
        return self.generate_story_continuation(prompt, f"in a {environment}", max_length=100)
    
    def generate_npc_dialogue(self, npc_type="innkeeper", context=""):
        """Generate NPC dialogue."""
        self._initialize_model()
        
        if not self._llm_available:
            return self.rule_based_generator.generate_npc_dialogue(npc_type, context)
        
        prompt = f"The {npc_type} says:"
        return self.generate_story_continuation(prompt, context, max_length=80)

class RuleBasedStoryGenerator:
    """Fallback rule-based story generator for when LLM is not available."""
    
    def __init__(self):
        self.story_elements = [
            "ancient ruins",
            "mysterious fog",
            "abandoned village", 
            "dark forest",
            "hidden cave",
            "old tower",
            "forgotten temple",
            "cursed graveyard"
        ]
        
        self.encounters = [
            "a group of bandits",
            "a wounded traveler",
            "strange footprints",
            "an abandoned camp",
            "a mysterious shrine",
            "wild animals",
            "a lost merchant",
            "signs of recent battle"
        ]
        
        self.actions = [
            "investigates carefully",
            "moves forward cautiously", 
            "stops to listen",
            "examines the area",
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
            "Something important happened here recently.",
            "The adventure takes an unexpected turn.",
            "Danger seems to lurk around every corner.",
            "New possibilities present themselves.",
            "The stakes have suddenly become much higher."
        ]
    
    def generate_story_continuation(self, prompt, character_context=""):
        """Generate a story continuation using rule-based approach."""
        # Simple template-based generation
        story_part = random.choice([
            f"As they explore, the atmosphere becomes {random.choice(self.atmospheres)}. "
            f"The party {random.choice(self.actions)} and discovers {random.choice(self.discoveries)}. "
            f"{random.choice(self.outcomes)}",
            
            f"Moving deeper into the area, they come across {random.choice(self.encounters)}. "
            f"The group {random.choice(self.movements)} while staying alert. "
            f"Suddenly, they {random.choice(self.encounters)}. {random.choice(self.outcomes)}",
            
            f"The environment around them shifts as they discover {random.choice(self.story_elements)}. "
            f"With careful observation, they notice {random.choice(self.discoveries)}. "
            f"This revelation suggests that {random.choice(self.outcomes).lower()}"
        ])
        
        return story_part
    
    def generate_encounter(self, character_level=1, environment="forest"):
        """Generate an encounter appropriate for character level."""
        difficulty = "easy" if character_level <= 2 else "moderate" if character_level <= 5 else "challenging"
        
        encounter_types = {
            "easy": ["a lone wolf", "a group of goblins", "a suspicious merchant", "bandits demanding toll"],
            "moderate": ["an orc war party", "a territorial owlbear", "a group of cultists", "a dangerous magical trap"],
            "challenging": ["a young dragon", "a powerful wizard", "an undead legion", "a demon summoning ritual"]
        }
        
        encounter = random.choice(encounter_types[difficulty])
        return f"As the party travels through the {environment}, they encounter {encounter}. " \
               f"The situation requires careful consideration and quick thinking. " \
               f"{random.choice(self.outcomes)}"
    
    def generate_npc_dialogue(self, npc_type="innkeeper", context=""):
        """Generate NPC dialogue."""
        dialogues = {
            "innkeeper": [
                "Welcome to my tavern! What brings you to these parts?",
                "You look like you've traveled far. Can I offer you a room and a meal?",
                "Strange things have been happening around here lately...",
                "I've heard rumors of adventure in the nearby ruins."
            ],
            "merchant": [
                "I have the finest goods from across the realm!",
                "Perhaps you're interested in some magical items?",
                "Trade has been dangerous lately with all the bandits about.",
                "I might have something special for experienced adventurers like yourselves."
            ],
            "guard": [
                "Halt! State your business in the city.",
                "Things have been quiet... too quiet, if you ask me.",
                "The captain has been asking about skilled adventurers.",
                "Stay alert. There have been reports of trouble brewing."
            ]
        }
        
        return random.choice(dialogues.get(npc_type, dialogues["innkeeper"]))

# Create a global instance for backward compatibility
story_generator = StorySystem()