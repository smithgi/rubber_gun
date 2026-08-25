import logging
import sys
from ollama import chat

logger = logging.getLogger(__name__)
from ollama import ChatResponse
import pyttsx3


class AlarmAgent:
    def __init__(self, model="llama3"):
        self.model = model

    def speak_alarm(self, sensor_data, prompt_file="prompts/alarm.prompt"):
        with open(prompt_file, "r") as f:
            system_prompt = f.read()

        sensor_data = sensor_data

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "{}".format(sensor_data)}
        ]
        response = chat(model=self.model, messages=messages, stream=False)
        alarm_text = response['message']['content']
        alarm_text = alarm_text.replace("None", "")
        logger.info("Alarm response: %s", response['message']['content'])

        engine = pyttsx3.init()
        engine.say(alarm_text)
        engine.runAndWait()


    def check_status(self, sensor_data, prompt_file="prompts/check_status.prompt"):
        with open(prompt_file, "r") as f:
            system_prompt = f.read()

        logger.debug("Sensor data: %s", sensor_data)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "{}".format(sensor_data)}
        ]
        response = chat(model=self.model, messages=messages, stream=False)
        alarm_text = response['message']['content']
        alarm_text = alarm_text.replace("None", "")
        logger.info("Status check: %s", alarm_text)

        #engine = pyttsx3.init()
        #engine.say(alarm_text)
        #engine.runAndWait()



        # or access fields directly from the response object
        #print(response.message.content)


if __name__ == "__main__":
    sensor_data = sys.argv[1]
    speaker = AlarmAgent()
    res = speaker.speak_alarm(sensor_data)
    logger.info("Result: %s", res)
