#!/bin/bash
# Daemon: keep trying to create an A1.Flex instance until capacity is available.
# Cycles through all 3 ADs every 2 minutes.
# Run on the Oracle VM: nohup bash wait_for_instance.sh &

COMPARTMENT="ocid1.tenancy.oc1..aaaaaaaarq7lhfollffeeftnph3mfw2vbmkkw6eh6bnvowopfsgmkbk2rwbq"
IMAGE="ocid1.image.oc1.eu-frankfurt-1.aaaaaaaasoblespfnzqa67jnq4psbpnbal4mlh2tpwnlhnhvmkhzuqbrxu4a"
SUBNET="ocid1.subnet.oc1.eu-frankfurt-1.aaaaaaaabiq5ajl4y3girrlyenroxjditowa6slsbc26i3ekl4ci3aobb7qq"
SHAPE="VM.Standard.A1.Flex"
DISPLAY_NAME="xdownloader-bot"
SSH_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC77R+v/tb+3bFYgh9O6F3GRhyMJpgQkfKZOTl46lmG2OOqZOD9/OiZMGx0QHimhGZMNca21meLEfHg0NZbZ8VKWX+lvq4b6464RTJDA+YAS1pj3jAU/IGogjC0moMgjvh39iJNOKfkY9atioV0J7zg7uUaHjliwy9RL+21AROCdXOAICNvmMe5A8nO2klPldA8EGW/2/X+rKy9k4xNl0eq2yL4fQptfmAeMgBOQYwElGkkM1FBzeblPqrPhfdXxVoOeDsFz+JlhtwTxKV3xG/WJM7vmBBVw7GCU3h84NkZCli2NkxitWwHbeeB41omIgbigmmOI3MZCdoHGKFHWox5 ssh-key-2026-03-28"

ADS=(
  "Dvah:EU-FRANKFURT-1-AD-1"
  "Dvah:EU-FRANKFURT-1-AD-2"
  "Dvah:EU-FRANKFURT-1-AD-3"
)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$SCRIPT_DIR/../wait_for_instance.log"

echo "$(date): Starting instance availability daemon" | tee -a "$LOG"
echo "Shape: $SHAPE (2 OCPUs, 12 GB RAM)" | tee -a "$LOG"
echo "Checking every 2 minutes across 3 ADs..." | tee -a "$LOG"

while true; do
  for AD in "${ADS[@]}"; do
    echo "$(date): Trying $AD..." | tee -a "$LOG"

    RESULT=$(oci compute instance launch \
      --compartment-id "$COMPARTMENT" \
      --availability-domain "$AD" \
      --shape "$SHAPE" \
      --shape-config '{"ocpus": 2, "memoryInGBs": 12}' \
      --image-id "$IMAGE" \
      --subnet-id "$SUBNET" \
      --display-name "$DISPLAY_NAME" \
      --assign-public-ip true \
      --metadata "{\"ssh_authorized_keys\": \"$SSH_KEY\"}" \
      2>&1)

    if echo "$RESULT" | grep -q '"lifecycle-state"'; then
      echo "$(date): SUCCESS! Instance created in $AD" | tee -a "$LOG"
      echo "$RESULT" | tee -a "$LOG"

      # Extract instance ID and wait for public IP
      INSTANCE_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")
      echo "Instance ID: $INSTANCE_ID" | tee -a "$LOG"

      echo "Waiting for instance to get public IP..." | tee -a "$LOG"
      sleep 60
      VNIC_ID=$(oci compute vnic-attachment list --compartment-id "$COMPARTMENT" --instance-id "$INSTANCE_ID" --query 'data[0]."vnic-id"' --raw-output 2>&1)
      PUBLIC_IP=$(oci network vnic get --vnic-id "$VNIC_ID" --query 'data."public-ip"' --raw-output 2>&1)
      echo "$(date): Public IP: $PUBLIC_IP" | tee -a "$LOG"

      echo "" | tee -a "$LOG"
      echo "============================================" | tee -a "$LOG"
      echo "INSTANCE READY!" | tee -a "$LOG"
      echo "IP: $PUBLIC_IP" | tee -a "$LOG"
      echo "SSH: ssh -i <key> ubuntu@$PUBLIC_IP" | tee -a "$LOG"
      echo "============================================" | tee -a "$LOG"
      exit 0
    fi

    if echo "$RESULT" | grep -q "Out of host capacity"; then
      echo "$(date): $AD - No capacity" | tee -a "$LOG"
    else
      echo "$(date): $AD - Error: $(echo "$RESULT" | grep -o '"message": "[^"]*"')" | tee -a "$LOG"
    fi

    sleep 10  # Brief pause between ADs
  done

  echo "$(date): All ADs full. Waiting 2 minutes..." | tee -a "$LOG"
  sleep 120
done
