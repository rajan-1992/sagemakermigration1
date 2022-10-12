
FROM python:3.7-slim-buster

RUN apt-get update \
      && apt-get install -y \
      # build-essential \
      curl zip unzip

RUN pip3 install pandas==0.25.3 scikit-learn==0.21.3 boto3==1.18.21 sagemaker==2.48.1 \
		boto3

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    &&   unzip -q awscliv2.zip \
    &&   ./aws/install
    
ENV PYTHONUNBUFFERED=TRUE

ENTRYPOINT ["python3"]

