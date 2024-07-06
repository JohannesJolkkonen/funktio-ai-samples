
# Continuously ping a dummy stream of numerical readings. 
# In the final demo, this will be reading values from timescaleDB where values are being added in real-time
# So I will probably have a program running locally that simulates a sensor device, that sends readings and can also 
# receive requests, such as restarting the device or changing the device settings. I might even have a UI to control this device, 
# such as being able to trigger failure modes and observe the behavior 

"""
So it might be that I have the device simulator running in an UI, and the agent running in my IDE. Or, I 
could have the agent running in its own UI -- OR, I could have them both running in the same UI. That's probably the ideal way. 
"""

# Based on numerical reading values, graph the data in a UI, with some thresholds that trigger actions
# The actions will have some instructions for the LLM-agent what options it has to handle the situation
# Action A (idea):
    # - Read device-logs from another Timescale DB
    # - Process the logs with LLM to get more info about the issue
    # - this action will typically be the first step in whatever other action the model takes

# Action B:
    # - Restart the device? Not sure how to simulate this
    # - This action will typically be the second step
# Action C:
    # - Send a message to a chatbot to get more info about the issue
