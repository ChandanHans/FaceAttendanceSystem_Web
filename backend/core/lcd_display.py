"""
I2C LCD Display Module for 16x2 Character Display
Shows recognized person names on physical LCD screen
"""
import logging
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
        self.last_name = None
        
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
        except Exception as e:
            logging.error(f"LCD write error: {e}")
            self.enabled = False
    
    def show_name(self, name: str, role: str = ""):
        """
        Display person's name and role on LCD
        
        Args:
            name: Person's name (max 16 chars for line 1)
            role: Person's role (max 16 chars for line 2)
        """
        if not self.enabled:
            return
        
        # Avoid duplicate updates
        display_text = f"{name}|{role}"
        if display_text == self.last_name:
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
            
            self.last_name = display_text
            logging.debug(f"LCD: {name} ({role})")
            
        except Exception as e:
            logging.error(f"LCD write error: {e}")
            self.enabled = False
    
    def show_unknown(self):
        """Display message for unknown person"""
        if not self.enabled:
            return
        
        try:
            self.lcd.clear()
            self.lcd.write_string("Unknown Person\n\rAccess Denied")
            self.last_name = "unknown"
        except Exception as e:
            logging.error(f"LCD write error: {e}")
            self.enabled = False
    
    def show_waiting(self):
        """Display waiting/scanning message"""
        if not self.enabled:
            return
        
        try:
            self.lcd.clear()
            self.lcd.write_string("Scanning...\n\rLook at camera")
            self.last_name = "waiting"
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
            
            self.last_name = None  # Allow update next time
        except Exception as e:
            logging.error(f"LCD write error: {e}")
            self.enabled = False
    
    def clear(self):
        """Clear the display"""
        if not self.enabled:
            return
        
        try:
            self.lcd.clear()
            self.last_name = None
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
