
FROM python:3.7-slim-buster

RUN pip3 install pandas==0.25.3 scikit-learn==0.21.3 boto3==1.18.21 sagemaker==2.48.1 \
		boto3

ENV PYTHONUNBUFFERED=TRUE

ENTRYPOINT ["python3"]

