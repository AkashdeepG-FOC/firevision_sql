#!/usr/bin/env python3
"""
Fix icon issues in enhanced_fullscreen_widget.py
"""

def fix_icon_issues():
    with open('enhanced_fullscreen_widget.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the people detection button line
    content = content.replace(
        'self.set_button_icon(self.people_detection_btn, "assests/icons/people.png", "�"))',
        'self.set_button_icon(self.people_detection_btn, "assests/icons/people.png", "👥")'
    )
    
    # Also fix any other Unicode issues
    content = content.replace('�', '👥')
    
    with open('enhanced_fullscreen_widget.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed icon issues in enhanced_fullscreen_widget.py")

if __name__ == "__main__":
    fix_icon_issues()