# Security Architecture

Heidi Engine is built with a zero-trust philosophy.

## Trainer Firewall
The training component only accepts datasets that have been explicitly signed and verified by the validation layer.

## Signature Verification
All data receipts are cryptographically signed. If a receipt is tampered with, the pipeline halts.

## Localhost Binding
The HTTP control API binds strictly to `127.0.0.1` to prevent unauthorized remote access.

## Journal Hash Chaining
Every event in the journal includes a hash of the previous event, creating an immutable audit trail of the training process.
