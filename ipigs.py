import time
import json
import os
import pygame
from dataclasses import dataclass, field
from typing import List, Callable, Optional
from pygame.locals import *

# Enhanced Constants
SCREEN_SIZE = (1280, 720)
SAVE_FILE = "iseps_save.json"
BASE_COLORS = {
    "background": (15, 20, 25),
    "text": (240, 240, 240),
    "text_disabled": (100, 100, 100),
    "particle_alpha": (100, 200, 255),
    "particle_beta": (255, 150, 100),
    "particle_gamma": (150, 255, 100),
    "button": (50, 60, 70),
    "button_hover": (70, 80, 90),
    "button_disabled": (40, 45, 50),
    "panel_background": (30, 35, 40),
    "achievement": (255, 215, 0),
    "success": (100, 255, 100),
    "error": (255, 100, 100),
}

@dataclass
class ParticleType:
    name: str
    base_cost: float
    cost_growth: float
    base_production: float
    produces: str
    color: tuple
    count: float = 0.0  # Changed to float for fractional values
    upgrades: List[str] = field(default_factory=list)
    description: str = ""
    unlocked: bool = True

    def calculate_cost(self) -> float:
        max_exponent = 1000  # Cap exponent to prevent overflow
        exponent = max_exponent if self.count > max_exponent else self.count
        raw_cost = self.base_cost * (self.cost_growth ** exponent)
        return round(raw_cost, 2)  # Round to 2 decimal places

    def calculate_production_per_second(self, prestige_bonus: float) -> float:
        # For beta particles, add a small base production even if count is 0
        if self.name.lower() == "beta" and self.count == 0:
            print("Beta is producing with a base rate!")
            return 3.0 * prestige_bonus  # or 3.3 * prestige_bonus if you prefer
    
        if not self.upgrades:
            return self.count * self.base_production * prestige_bonus
        
        total_production = self.count * self.base_production * prestige_bonus
        for upgrade_name in self.upgrades:
        # Apply some growth logic here, based on the upgrade
        # (For example, for each upgrade, increase production by a fixed percentage)
            total_production *= 1.05  # This is just an example, adjust as needed

        return total_production
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "base_cost": self.base_cost,
            "cost_growth": self.cost_growth,
            "base_production": self.base_production,
            "produces": self.produces,
            "color": self.color,
            "count": self.count,
            "upgrades": self.upgrades,
            "description": self.description,
            "unlocked": self.unlocked
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ParticleType":
        return cls(
            name=data["name"],
            base_cost=data["base_cost"],
            cost_growth=data["cost_growth"],
            base_production=data["base_production"],
            produces=data["produces"],
            color=tuple(data["color"]),
            count=data["count"],
            upgrades=data.get("upgrades", []),
            description=data.get("description", ""),
            unlocked=data.get("unlocked", True)
        )

@dataclass
class Achievement:
    name: str
    description: str
    condition: Callable[["GameState"], bool]
    reward: float
    unlocked: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "reward": self.reward,
            "unlocked": self.unlocked
        }

@dataclass
class Upgrade:
    name: str
    cost: float
    cost_growth: float
    effect: Callable
    description: str
    particle_requirement: str
    currency: str = 'cash'
    unlocked: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cost": self.cost,
            "cost_growth": self.cost_growth,
            "description": self.description,
            "particle_requirement": self.particle_requirement,
            "currency": self.currency,
            "unlocked": self.unlocked
        }

class GameState:
    def __init__(self):
        self.cash: float = 50.0
        self.prestige_level: int = 0
        self.prestige_bonus: float = 1.0
        self.last_update: float = time.time()
        self.total_earnings: float = 0.0
        
        self.init_particles()
        self.init_achievements()
        self.init_upgrades()

    def init_particles(self):
        self.particles = {
            "alpha": ParticleType(
                name="Alpha",
                base_cost=10,
                cost_growth=1.15,
                base_production=1.0,
                produces="cash",
                color=BASE_COLORS["particle_alpha"],
                description="Basic quantum particle, stable and reliable.",
                upgrades=["Quantum Alignment", "Entanglement Boost"]
            ),
            "beta": ParticleType(
                name="Beta",
                base_cost=50,
                cost_growth=1.2,
                base_production=3.0,
                produces="beta",
                color=BASE_COLORS["particle_beta"],
                description="Generates Beta particles which boost Alpha production via upgrades.",
                upgrades=["Tachyon Acceleration", "Chronal Syncing"],
                unlocked=False
            ),
            "gamma": ParticleType(
                name="Gamma",
                base_cost=250,
                cost_growth=1.25,
                base_production=10.0,
                produces="gamma",
                color=BASE_COLORS["particle_gamma"],
                description="Highly energetic particle used to boost Beta production.",
                unlocked=False
            )
        }

    def init_achievements(self):
        self.achievements = [
            Achievement(
                name="Quantum Pioneer",
                description="Produce your first Alpha particle",
                condition=lambda state: any(p.count > 0 for p in state.particles.values()),
                reward=1.1
            ),
            Achievement(
                name="Particle Magnate",
                description="Own 50 total particles",
                condition=lambda state: sum(p.count for p in state.particles.values()) >= 50,
                reward=1.2
            ),
            Achievement(
                name="Master of Energy",
                description="Reach $1,000,000 total earnings",
                condition=lambda state: state.total_earnings >= 1_000_000,
                reward=1.5
            )
        ]

    def init_upgrades(self):
        self.upgrades = [
            Upgrade(
                name="Quantum Computing",
                cost=100,
                cost_growth=1.5,
                effect=self.apply_quantum_computing,
                description="Doubles Alpha particle production",
                particle_requirement="alpha",
                currency="cash"
            ),
            Upgrade(
                name="Hyperspace Fabrication",
                cost=500,
                cost_growth=1.8,
                effect=self.apply_hyperspace_fabrication,
                description="Triples Beta particle output",
                particle_requirement="beta",
                currency="cash"
            ),
            Upgrade(
                name="Gamma Resonance",
                cost=2500,
                cost_growth=2.0,
                effect=self.apply_gamma_resonance,
                description="Quadruples Gamma particle output",
                particle_requirement="gamma",
                currency="cash"
            )
        ]
        
        self.booster_upgrades = [
            Upgrade(
                name="Beta Booster",
                cost=10,
                cost_growth=1.2,
                effect=self.apply_beta_booster,
                description="Boosts Alpha particle production by 10%",
                particle_requirement="beta",
                currency="beta"
            ),
            Upgrade(
                name="Gamma Booster",
                cost=50,
                cost_growth=1.3,
                effect=self.apply_gamma_booster,
                description="Boosts Beta particle production by 15%",
                particle_requirement="gamma",
                currency="gamma"
            )
        ]
        
        for upgrade_list in [self.upgrades, self.booster_upgrades]:
            for upgrade in upgrade_list:
                if upgrade.particle_requirement not in self.particles:
                    print(f"Warning: Upgrade {upgrade.name} references non-existent particle type {upgrade.particle_requirement}")
                    continue
                
                particle = self.particles[upgrade.particle_requirement]
                if upgrade.name not in particle.upgrades:
                    particle.upgrades.append(upgrade.name)
                
    def apply_quantum_computing(self):
        self.particles["alpha"].base_production *= 2

    def apply_hyperspace_fabrication(self):
        self.particles["beta"].base_production *= 3

    def apply_gamma_resonance(self):
        self.particles["gamma"].base_production *= 4

    def apply_beta_booster(self):
        self.particles["alpha"].base_production *= 1.1

    def apply_gamma_booster(self):
        self.particles["beta"].base_production *= 1.15

    def time_since_last_update(self) -> float:
        return time.time() - self.last_update

    def update_economy(self, time_diff: Optional[float] = None) -> Optional[List[str]]:
        if time_diff is None:
            time_diff = self.time_since_last_update()
            
            total_cash_earned = 0.0
            unlock_messages = []

        for particle in self.particles.values():
            if not particle.unlocked:
                continue
            production_per_second = particle.calculate_production_per_second(self.prestige_bonus)
            produced = production_per_second * time_diff

            if particle.produces == "cash":
                self.cash += produced
                total_cash_earned += produced
            else:
                    if particle.produces in self.particles:
                        self.particles[particle.produces].count += produced
                        self.particles[particle.produces].count = round(self.particles[particle.produces].count, 2)  # Prevent runaway growth# Fixed this line
                    else:
                        print(f"Warning: Particle {particle.name} produces unknown type {particle.produces}")

        self.total_earnings += total_cash_earned
        self.last_update = time.time()

        if self.total_earnings >= 500 and not self.particles["beta"].unlocked:
            self.particles["beta"].unlocked = True
            unlock_messages.append("Beta particles unlocked! >>")
            if self.total_earnings >= 5000 and not self.particles["gamma"].unlocked:
                self.particles["gamma"].unlocked = True
            unlock_messages.append("Gamma particles unlocked! >>")

        return unlock_messages if unlock_messages else None
    

    def perform_prestige(self) -> bool:
        if self.cash >= 1000:
            self.prestige_level += 1
            self.prestige_bonus = 1 + 0.1 * self.prestige_level
            self.cash = 0
            for particle in self.particles.values():
                particle.count = 0
            return True
        return False

    def check_achievements(self) -> Optional[Achievement]:
        for achievement in self.achievements:
            if not achievement.unlocked and achievement.condition(self):
                achievement.unlocked = True
                self.prestige_bonus *= achievement.reward
                return achievement
        return None

    def ensure_default_particles(self):
        default_particles = {
            "alpha": ParticleType(
                name="Alpha",
                base_cost=10,
                cost_growth=1.15,
                base_production=1.0,
                produces="cash",
                color=BASE_COLORS["particle_alpha"],
                description="Basic quantum particle, stable and reliable.",
                upgrades=["Quantum Alignment", "Entanglement Boost"]
            ),
            "beta": ParticleType(
                name="Beta",
                base_cost=50,
                cost_growth=1.2,
                base_production=3.0,
                produces="beta",
                color=BASE_COLORS["particle_beta"],
                description="Advanced particle used to boost Alpha production via upgrades.",
                unlocked=False
            ),
            "gamma": ParticleType(
                name="Gamma",
                base_cost=250,
                cost_growth=1.25,
                base_production=10.0,
                produces="gamma",
                color=BASE_COLORS["particle_gamma"],
                description="Highly energetic particle used to boost Beta production.",
                unlocked=False
            )
        }
        for name, default_particle in default_particles.items():
            if name not in self.particles:
                self.particles[name] = default_particle

    def to_dict(self) -> dict:
        return {
            "cash": self.cash,
            "prestige_level": self.prestige_level,
            "prestige_bonus": self.prestige_bonus,
            "last_update": self.last_update,
            "total_earnings": self.total_earnings,
            "particles": {name: particle.to_dict() for name, particle in self.particles.items()},
            "upgrades": [upgrade.to_dict() for upgrade in self.upgrades],
            "booster_upgrades": [upgrade.to_dict() for upgrade in self.booster_upgrades],
            "achievements": [achievement.to_dict() for achievement in self.achievements]
        }

    def save(self):
        try:
            data = self.to_dict()
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Save error: {e}")

    def load(self):
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r") as f:
                    data = json.load(f)
                    
                    self.cash = data.get("cash", 50.0)
                    self.prestige_level = data.get("prestige_level", 0)
                    self.prestige_bonus = data.get("prestige_bonus", 1.0)
                    self.total_earnings = data.get("total_earnings", 0.0)
                    self.last_update = time.time()
                    
                    particles_data = data.get("particles", {})
                    self.particles = {
                        name: ParticleType.from_dict(particle_data)
                        for name, particle_data in particles_data.items()
                    }
                    
                    upgrades_data = data.get("upgrades", [])
                    for saved_upgrade in upgrades_data:
                        for upgrade in self.upgrades:
                            if upgrade.name == saved_upgrade["name"]:
                                upgrade.unlocked = saved_upgrade["unlocked"]
                                break
                    booster_upgrades_data = data.get("booster_upgrades", [])
                    for saved_upgrade in booster_upgrades_data:
                        for upgrade in self.booster_upgrades:
                            if upgrade.name == saved_upgrade["name"]:
                                upgrade.unlocked = saved_upgrade["unlocked"]
                                break
                    
                    achievements_data = data.get("achievements", [])
                    for saved_achievement in achievements_data:
                        for achievement in self.achievements:
                            if achievement.name == saved_achievement["name"]:
                                achievement.unlocked = saved_achievement["unlocked"]
                                break
                    self.ensure_default_particles()
        except Exception as e:
            print(f"Load error: {e}")

class GameUI:
    def __init__(self, game_state: GameState):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("ISEPS: Infinite Particle Engine")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.game = game_state
        self.messages = []

    def add_message(self, text: str, color: tuple = BASE_COLORS["text"]):
        self.messages.append({
            "text": text,
            "color": color,
            "time": time.time()
        })

    def format_number(self, num: float) -> str:
        if num >= 1_000_000:
            return f"{num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num/1_000:.2f}K"
        return f"{num:.2f}"

    def draw_button(self, rect: pygame.Rect, text: str, enabled: bool = True, hover: bool = False) -> None:
        if not enabled:
            color = BASE_COLORS["button_disabled"]
            text_color = BASE_COLORS["text_disabled"]
        else:
            color = BASE_COLORS["button_hover"] if hover else BASE_COLORS["button"]
            text_color = BASE_COLORS["text"]
            
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        text_surf = self.font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def draw_panel(self, rect: pygame.Rect, title: Optional[str] = None) -> float:
        pygame.draw.rect(self.screen, BASE_COLORS["panel_background"], rect, border_radius=8)
        if title:
            title_surf = self.font.render(title, True, BASE_COLORS["text"])
            self.screen.blit(title_surf, (rect.x + 10, rect.y + 5))
            return rect.y + 30
        return rect.y + 10

    def draw_achievement_panel(self):
        panel_rect = pygame.Rect(860, 60, 400, 300)
        y_offset = self.draw_panel(panel_rect, "Achievements")
        
        for achievement in self.game.achievements:
            achievement_rect = pygame.Rect(panel_rect.x + 10, y_offset, panel_rect.width - 20, 50)
            color = BASE_COLORS["achievement"] if achievement.unlocked else BASE_COLORS["button"]
            pygame.draw.rect(self.screen, color, achievement_rect, border_radius=5)
            
            name_surf = self.font.render(achievement.name, True, BASE_COLORS["text"])
            self.screen.blit(name_surf, (achievement_rect.x + 10, achievement_rect.y + 5))
            
            desc_surf = self.font.render(
                f"{achievement.description} (x{achievement.reward} bonus)",
                True,
                BASE_COLORS["text"]
            )
            self.screen.blit(desc_surf, (achievement_rect.x + 10, achievement_rect.y + 25))
            
            y_offset += 60

    def draw_particle_panel(self):
        panel_rect = pygame.Rect(20, 60, 400, 600)
        y_offset = self.draw_panel(panel_rect, "Particles")
        
        for particle in self.game.particles.values():
            text = f"{particle.name}: {particle.count:.1f}"  # Show 1 decimal place
            if not particle.unlocked:
                text += " (Locked)"
                text_surf = self.font.render(text, True, BASE_COLORS["text_disabled"])
                self.screen.blit(text_surf, (panel_rect.x + 10, y_offset))
                unlock_text = f"(Requires ${self.format_number(500 if particle.name == 'Beta' else 5000)} earned)"
                unlock_surf = self.font.render(unlock_text, True, BASE_COLORS["text_disabled"])
                self.screen.blit(unlock_surf, (panel_rect.x + 10, y_offset + 25))
                y_offset += 60
                continue
            
            production = particle.calculate_production_per_second(self.game.prestige_bonus)
            text += f" (${self.format_number(production)}/s)"
            text_surf = self.font.render(text, True, particle.color)
            self.screen.blit(text_surf, (panel_rect.x + 10, y_offset))
            desc_surf = self.font.render(particle.description, True, (150, 150, 150))
            self.screen.blit(desc_surf, (panel_rect.x + 10, y_offset + 25))
            
            btn_rect = pygame.Rect(panel_rect.x + 280, y_offset, 100, 30)
            mouse_pos = pygame.mouse.get_pos()
            hover = btn_rect.collidepoint(mouse_pos)
            cost = particle.calculate_cost()
            can_afford = self.game.cash >= cost
            btn_text = f"Buy (${self.format_number(cost)})"
            self.draw_button(btn_rect, btn_text, enabled=can_afford, hover=hover)
            y_offset += 60

    def draw_upgrade_section(self, panel_rect, y_offset, upgrades, title):
        title_surf = self.font.render(title, True, BASE_COLORS["text"])
        self.screen.blit(title_surf, (panel_rect.x + 10, y_offset))
        y_offset += 30
        
        for upgrade in upgrades:
            if upgrade.particle_requirement not in self.game.particles:
                continue
            required_particle = self.game.particles[upgrade.particle_requirement]
            if not required_particle.unlocked:
                continue
            
            upgrade_rect = pygame.Rect(panel_rect.x + 10, y_offset, panel_rect.width - 20, 50)
            mouse_pos = pygame.mouse.get_pos()
            hover = upgrade_rect.collidepoint(mouse_pos)
            
            if upgrade.unlocked:
                text = f"{upgrade.name} (Purchased)"
                self.draw_button(upgrade_rect, text, enabled=False)
            else:
                if upgrade.currency == 'cash':
                    can_afford = self.game.cash >= upgrade.cost
                    formatted_cost = f"${self.format_number(upgrade.cost)}"
                else:
                    particle_count = self.game.particles[upgrade.currency].count
                    can_afford = particle_count >= upgrade.cost
                    formatted_cost = f"{upgrade.cost} {upgrade.currency}"
                text = f"{upgrade.name} - {formatted_cost}"
                self.draw_button(upgrade_rect, text, enabled=can_afford, hover=hover)
            
            desc_surf = self.font.render(upgrade.description, True, (150, 150, 150))
            self.screen.blit(desc_surf, (upgrade_rect.x + 10, upgrade_rect.y + 30))
            y_offset += 60
        return y_offset

    def draw_upgrade_panel(self):
        panel_rect = pygame.Rect(440, 60, 400, 600)
        y_offset = self.draw_panel(panel_rect, "Upgrades")
        
        y_offset = self.draw_upgrade_section(panel_rect, y_offset, self.game.upgrades, "Regular Upgrades")
        y_offset += 20
        y_offset = self.draw_upgrade_section(panel_rect, y_offset, self.game.booster_upgrades, "Booster Upgrades")

    def draw_stats_panel(self):
        cash_text = f"Quantum Funds: ${self.format_number(self.game.cash)}"
        cash_surf = self.font.render(cash_text, True, (100, 200, 100))
        self.screen.blit(cash_surf, (20, 20))
        
        beta_text = f"Beta Particles: {self.game.particles['beta'].count:.1f}"  # Show 1 decimal
        beta_surf = self.font.render(beta_text, True, (200, 200, 200))
        self.screen.blit(beta_surf, (300, 20))
        
        gamma_text = f"Gamma Particles: {self.game.particles['gamma'].count:.1f}"  # Show 1 decimal
        gamma_surf = self.font.render(gamma_text, True, (200, 200, 200))
        self.screen.blit(gamma_surf, (500, 20))
        
        earnings_text = f"Total Earnings: ${self.format_number(self.game.total_earnings)}"
        earnings_surf = self.font.render(earnings_text, True, (200, 200, 200))
        self.screen.blit(earnings_surf, (700, 20))

    def draw_prestige_button(self):
        prestige_rect = pygame.Rect(SCREEN_SIZE[0] - 150, 20, 130, 40)
        mouse_pos = pygame.mouse.get_pos()
        hover = prestige_rect.collidepoint(mouse_pos)
        can_prestige = self.game.cash >= 1000
        text = f"Prestige (${self.format_number(1000)})"
        self.draw_button(prestige_rect, text, enabled=can_prestige, hover=hover)
        if self.game.prestige_level > 0:
            bonus_text = f"Prestige Bonus: x{self.format_number(self.game.prestige_bonus)}"
            bonus_surf = self.font.render(bonus_text, True, (200, 150, 255))
            self.screen.blit(bonus_surf, (SCREEN_SIZE[0] - 350, 30))

    def draw_messages(self):
        now = time.time()
        y_offset = SCREEN_SIZE[1] - 50
        
        for msg in self.messages[:]:
            if now - msg["time"] < 3:
                text_surf = self.font.render(msg["text"], True, msg["color"])
                text_rect = text_surf.get_rect(right=SCREEN_SIZE[0] - 20, bottom=y_offset)
                self.screen.blit(text_surf, text_rect)
                y_offset -= 30
            else:
                self.messages.remove(msg)

    def handle_click(self):
        mouse_pos = pygame.mouse.get_pos()
        
        prestige_rect = pygame.Rect(SCREEN_SIZE[0] - 150, 20, 130, 40)
        if prestige_rect.collidepoint(mouse_pos):
            if self.game.perform_prestige():
                self.add_message("Prestige achieved! Particles reset.", (200, 150, 255))
            else:
                self.add_message("Not enough funds for prestige!", BASE_COLORS["error"])
            return

        # Handle particle purchases
        panel_rect = pygame.Rect(20, 60, 400, 600)
        y_offset = panel_rect.y + 30
        
        for particle in self.game.particles.values():
            btn_rect = pygame.Rect(panel_rect.x + 280, y_offset, 100, 30)
            if btn_rect.collidepoint(mouse_pos):
                if not particle.unlocked:
                    continue
                cost = particle.calculate_cost()
                if self.game.cash >= cost:
                    self.game.cash -= cost
                    particle.count += 1
                    self.add_message(f"Acquired {particle.name} Particle!", particle.color)
                else:
                    self.add_message(f"Not enough funds for {particle.name} particle!", BASE_COLORS["error"])
            y_offset += 60

        # Handle upgrades with corrected positioning
        upgrade_panel_rect = pygame.Rect(440, 60, 400, 600)
        y_offset = upgrade_panel_rect.y + 30  # Start after panel title
        
        # Process regular upgrades
        section_title_height = 30
        y_offset += section_title_height  # "Regular Upgrades" title
        for upgrade in self.game.upgrades:
            self.process_upgrade_click(upgrade, upgrade_panel_rect, y_offset, mouse_pos)
            y_offset += 60
        
        # Add spacing between sections
        y_offset += 20  # Section spacing
        y_offset += section_title_height  # "Booster Upgrades" title
        
        # Process booster upgrades
        for upgrade in self.game.booster_upgrades:
            self.process_upgrade_click(upgrade, upgrade_panel_rect, y_offset, mouse_pos)
            y_offset += 60

    def process_upgrade_click(self, upgrade, panel_rect, y_offset, mouse_pos):
        if upgrade.particle_requirement not in self.game.particles:
            return
        required_particle = self.game.particles[upgrade.particle_requirement]
        if not required_particle.unlocked:
            return
        
        upgrade_rect = pygame.Rect(
            panel_rect.x + 10,
            y_offset,
            panel_rect.width - 20,
            50
        )
        
        if upgrade_rect.collidepoint(mouse_pos) and not upgrade.unlocked:
            currency_type = upgrade.currency
            if currency_type == 'cash':
                can_afford = self.game.cash >= upgrade.cost
            else:
                if currency_type not in self.game.particles:
                    return
                can_afford = self.game.particles[currency_type].count >= upgrade.cost
            
            if can_afford:
                if currency_type == 'cash':
                    self.game.cash -= upgrade.cost
                else:
                    self.game.particles[currency_type].count -= upgrade.cost
                upgrade.effect()
                upgrade.unlocked = True
                self.add_message(f"Upgrade purchased: {upgrade.name}", BASE_COLORS["success"])
            else:
                if currency_type == 'cash':
                    msg = f"Not enough funds for {upgrade.name}!"
                else:
                    msg = f"Not enough {currency_type} particles!"
                self.add_message(msg, BASE_COLORS["error"])

    def run(self):
        running = True
        while running:
            unlock_messages = self.game.update_economy()
            if unlock_messages:
                for msg in unlock_messages:
                    self.add_message(msg, BASE_COLORS["success"])
            achievement = self.game.check_achievements()
            if achievement:
                self.add_message(
                    f"Achievement unlocked: {achievement.name}! (x{achievement.reward} bonus)",
                    BASE_COLORS["achievement"]
                )
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == MOUSEBUTTONDOWN:
                    self.handle_click()
                elif event.type == KEYDOWN:
                    if event.key == K_s:
                        self.game.save()
                        self.add_message("Game saved!", BASE_COLORS["success"])

            self.screen.fill(BASE_COLORS["background"])
            self.draw_stats_panel()
            self.draw_prestige_button()
            self.draw_particle_panel()
            self.draw_upgrade_panel()
            self.draw_achievement_panel()
            self.draw_messages()
            
            pygame.display.flip()
            self.clock.tick(60)

        self.game.save()
        pygame.quit()

if __name__ == "__main__":
    delete_save_file = False  # Set to True to reset progress
    if delete_save_file and os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
    game_state = GameState()
    game_state.load()
    ui = GameUI(game_state)
    ui.run()
