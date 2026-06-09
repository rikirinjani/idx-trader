#!/bin/bash
kill $(lsof -t -i:8502) 2>/dev/null
sleep 1
export STREAMLIT_EMAIL=""
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
cd /home/rikirinjani/idx-trader
nohup streamlit run dashboard.py --server.headless true --server.port 8502 > /tmp/streamlit_bot.log 2>&1 &
echo $! > /tmp/streamlit_bot.pid
echo "Bot dashboard PID: $(cat /tmp/streamlit_bot.pid)"
