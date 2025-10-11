#!/bin/bash

# Oreno GRC Notification System Cron Setup Script
# This script helps set up cron jobs for the intelligent notification system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Oreno GRC Notification System Setup ===${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found. Please run this script from the Oreno project root directory.${NC}"
    exit 1
fi

# Get project path
PROJECT_PATH=$(pwd)
echo -e "${GREEN}Project path: ${PROJECT_PATH}${NC}"

# Get Python path
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    PYTHON_PATH=$(which python)
fi

if [ -z "$PYTHON_PATH" ]; then
    echo -e "${RED}Error: Python not found in PATH${NC}"
    exit 1
fi

echo -e "${GREEN}Python path: ${PYTHON_PATH}${NC}"

# Check if virtual environment is active
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}Virtual environment: ${VIRTUAL_ENV}${NC}"
    PYTHON_PATH="$VIRTUAL_ENV/bin/python"
else
    echo -e "${YELLOW}Warning: No virtual environment detected. Using system Python.${NC}"
fi

# Create log directory
LOG_DIR="/var/log/oreno"
echo -e "${BLUE}Creating log directory: ${LOG_DIR}${NC}"

if [ ! -d "$LOG_DIR" ]; then
    sudo mkdir -p "$LOG_DIR"
    sudo chown $(whoami):$(whoami) "$LOG_DIR"
    echo -e "${GREEN}Log directory created and permissions set${NC}"
else
    echo -e "${GREEN}Log directory already exists${NC}"
fi

# Test the notification system
echo -e "${BLUE}Testing notification system...${NC}"
echo ""

echo -e "${YELLOW}Running dry-run test for compliance obligations...${NC}"
$PYTHON_PATH manage.py send_obligation_notifications --dry-run

echo ""
echo -e "${YELLOW}Running dry-run test for contract milestones...${NC}"
$PYTHON_PATH manage.py send_milestone_notifications --dry-run

echo ""
echo -e "${YELLOW}Running dry-run test for all notifications...${NC}"
$PYTHON_PATH manage.py send_all_notifications --dry-run

echo ""
echo -e "${GREEN}All tests completed successfully!${NC}"

# Generate cron job entries
echo ""
echo -e "${BLUE}=== Cron Job Setup ===${NC}"
echo ""
echo -e "${YELLOW}Choose your notification schedule:${NC}"
echo "1. Daily at 9:00 AM (recommended)"
echo "2. Twice daily (9:00 AM and 2:00 PM)"
echo "3. Custom schedule"
echo "4. Skip cron setup"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        CRON_SCHEDULE="0 9 * * *"
        CRON_DESC="Daily at 9:00 AM"
        ;;
    2)
        CRON_SCHEDULE="0 9,14 * * *"
        CRON_DESC="Daily at 9:00 AM and 2:00 PM"
        ;;
    3)
        echo -e "${YELLOW}Enter cron schedule (e.g., '0 9 * * *' for daily at 9 AM):${NC}"
        read -p "Cron schedule: " CRON_SCHEDULE
        CRON_DESC="Custom schedule: $CRON_SCHEDULE"
        ;;
    4)
        echo -e "${YELLOW}Skipping cron setup${NC}"
        CRON_SCHEDULE=""
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

if [ -n "$CRON_SCHEDULE" ]; then
    echo ""
    echo -e "${BLUE}Setting up cron job...${NC}"
    
    # Create cron job entry
    CRON_ENTRY="$CRON_SCHEDULE cd $PROJECT_PATH && $PYTHON_PATH manage.py send_all_notifications >> $LOG_DIR/notifications.log 2>&1"
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    
    echo -e "${GREEN}Cron job added successfully!${NC}"
    echo -e "${GREEN}Schedule: $CRON_DESC${NC}"
    echo -e "${GREEN}Command: $PYTHON_PATH manage.py send_all_notifications${NC}"
    echo -e "${GREEN}Log file: $LOG_DIR/notifications.log${NC}"
    
    echo ""
    echo -e "${BLUE}Current crontab:${NC}"
    crontab -l | grep -E "(send_all_notifications|send_obligation_notifications|send_milestone_notifications)" || echo "No notification cron jobs found"
fi

echo ""
echo -e "${BLUE}=== Setup Complete ===${NC}"
echo ""
echo -e "${GREEN}✅ Notification system is ready!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Ensure Celery worker is running: celery -A config worker --loglevel=info"
echo "2. Monitor logs: tail -f $LOG_DIR/notifications.log"
echo "3. Test manually: $PYTHON_PATH manage.py send_all_notifications --dry-run"
echo ""
echo -e "${BLUE}For more information, see: NOTIFICATION_SYSTEM_SETUP.md${NC}"
echo ""
echo -e "${GREEN}Setup completed successfully! 🎉${NC}"
