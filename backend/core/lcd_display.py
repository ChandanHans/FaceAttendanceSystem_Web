"""
I2C LCD Display Module for 16x2 Character Display
Shows recognized person names on physical LCD screen
"""
import logging
import threading
from typing import Optional

try:
    from RPLCD.i2c import CharLCD
    LCD_AVAILABLE = True
except ImportError:
    LCD_AVAILABLE = False
    logging.warning("RPLCD library not found. LCD display disabled.")

class LCDDisplay:
    """Manages 16x2 I2C LCD display for showing face recognition results"""
    
    def __init__(self, i2c_expander: str = 'PCF8574', address: int = 0x27, port: int = 1):
        """
        Initialize LCD display
        
        Args:
            i2c_expander: Type of I2C expander (PCF8574 or MCP23008)
            address: I2C address (common: 0x27, 0x3f)
            port: I2C port (1 for newer Pi, 0 for very old models)
        """
        self.lcd = None
        self.enabled = False
        self.last_person_id = None  # Track currently displayed person
        self.clear_timer = None
        self.display_timeout = 5  # Clear display after 5 seconds
        
        if not LCD_AVAILABLE:
            logging.info("LCD display disabled - RPLCD not installed")
            return
        
        try:
            self.lcd = CharLCD(
                i2c_expander=i2c_expander,
                address=address,
                port=port,
                cols=16,
                rows=2,
                dotsize=8,
                charmap='A02',
                auto_linebreaks=True
            )
            self.enabled = True
            self.show_startup_message()
            logging.info(f"LCD display initialized at address 0x{address:02x}")
        except Exception as e:
            logging.warning(f"Could not initialize LCD display: {e}")
            self.enabled = False
    
    def show_startup_message(self):
        """Display startup message"""
        if not self.enabled:
            return
        
        try:
            self.lcd.clear()
            self.lcd.write_string("Face Attendance\n\rSystem Ready")
            logging.info("✅ LCD startup message displayed")
        except Exception as e:
            logging.error(f"❌ LCD write error: {e}")
            self.enabled = False
    
    def show_name(self, name: str, role: str = "", person_id: str = ""):
        """
        Display person's name and role on LCD
        
        Args:
            name: Person's name (max 16 chars for line 1)
            role: Person's role (max 16 chars for line 2)
            person_id: Person's ID to track who is displayed
        """
        if not self.enabled:
            return
        
        # Cancel any pending clear timer
        if self.clear_timer:
            self.clear_timer.cancel()
        
        # If same person detected, just reset the timer (don't update display)
        if person_id and person_id == self.last_person_id:
            self.clear_timer = threading.Timer(self.display_timeout, self._auto_clear)
            self.clear_timer.start()
            return
        
        try:
            self.lcd.clear()
            
            # Line 1: Name (truncate if too long)
            line1 = name[:16] if len(name) <= 16 else name[:13] + "..."
            self.lcd.write_string(line1)
            
            # Line 2: Role or welcome message
            if role:
                line2 = role[:16] if len(role) <= 16 else role[:13] + "..."
                self.lcd.write_string(f"\n\r{line2}")
            else:
                self.lcd.write_string("\n\rWelcome!")
            
            self.last_person_id = person_id if person_id else name
            logging.debug(f"LCD: {name} ({role})")
            
            # Schedule auto-clear after timeout
            self.clear_timer = threading.Timer(self.display_timeout, self._auto_clear)
            self.clear_timer.start()
            
        except Exception as e:
            logging.error(f"LCD write error: {e}")
            self.enabled = False
    
    def _auto_clear(self):
        """Automatically clear display after timeout"""
        if not self.enabled:
            return
        try:
            self.lcd.clear()
            self.last_person_id = None
            logging.debug("LCD auto-cleared")
        except Exception as e:
            logging.error(f"LCD auto-clear error: {e}")
    
    def show_waiting(self):
        """Display waiting/scanning message"""
        if not self.enabled:
            return
        
        try:
            self.lcd.clear()
            self.lcd.write_string("Scanning...\n\rLook at camera")
            self.last_person_id = None
        except Exception as e:
            logging.error(f"LCD write error: {e}")
            self.enabled = False
    
    def show_message(self, line1: str, line2: str = ""):
        """
        Display custom message
        
        Args:
            line1: First line text (max 16 chars)
            line2: Second line text (max 16 chars)
        """
        if not self.enabled:
            return
        
        try:
            self.lcd.clear()
            line1 = line1[:16]
            self.lcd.write_string(line1)
            
            if line2:
                line2 = line2[:16]
                self.lcd.write_string(f"\n\r{line2}")
            
            self.last_person_id = None  # Allow update next time
        except Exception as e:
            logging.error(f"LCD write error: {e}")
            self.enabled = False
    
    def clear(self):
        """Clear the display"""
        if not self.enabled:
            return
        
        try:
            self.lcd.clear()
            self.last_person_id = None
        except Exception as e:
            logging.error(f"LCD write error: {e}")
            self.enabled = False
    
    def close(self):
        """Close LCD connection"""
        if self.enabled and self.lcd:
            try:
                self.lcd.clear()
                self.lcd.close()
                logging.info("LCD display closed")
            except:
                pass
