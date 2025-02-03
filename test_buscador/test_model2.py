import dspy
import warnings
warnings.filterwarnings("ignore", message="")

class SampleSignature(dspy.Signature):
    question: str = dspy.InputField(desc="¿Cuanto es 1 + 1?")
    response: str = dspy.OutputField(desc="La respuesta es 2")

lm = dspy.LM(
            model="openai//root/models/DeepSeek-R1-Distill-Qwen-14B",
            api_key="None",
            api_base="http://localhost:4891/v1",
            max_tokens=2000,
            temperature=0.10,
            cache=False
        )
dspy.configure(lm=lm)
qa = dspy.ChainOfThought(SampleSignature)
# or
qa = dspy.Predict(SampleSignature)


result = qa(question="escrive un ensayo sobre inteligencia artificial de 500 palabras ")

#print(result)
#type(result)

print("______________________________")
print(result.response)
#print(type(result.response))
print("______________________________\n")
