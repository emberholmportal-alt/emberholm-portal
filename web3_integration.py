"""
🔥 EMBERHOLM PORTAL - WEB3 INTEGRATION MODULE
==============================================

Módulo para integración con smart contract de Emberholm Portal.
Maneja staking/unstaking de NFTs de forma gasless (backend paga el gas).

Features:
- Stake/unstake NFTs on-chain
- Verificación de firmas off-chain
- Manejo de errores y reintentos
- Logging completo

Author: Emberholm Team
Version: 1.0
"""

import os
import time
import logging
from typing import Optional, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError, TimeExhausted
from eth_account.messages import encode_defunct
import json

logger = logging.getLogger(__name__)


class Web3Manager:
    """
    Gestor de interacciones con el smart contract de Emberholm Portal.
    """

    def __init__(self):
        """Inicializa conexión con blockchain."""
        # RPC URL (Base Mainnet o Sepolia para testing)
        self.rpc_url = os.getenv("WEB3_RPC_URL")
        if not self.rpc_url:
            raise ValueError("WEB3_RPC_URL not set in environment")

        # Conectar a blockchain
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {self.rpc_url}")

        logger.info(f"✅ Connected to blockchain: {self.rpc_url}")
        logger.info(f"📊 Chain ID: {self.w3.eth.chain_id}")

        # Mission Manager wallet (paga el gas)
        self.mission_manager_address = os.getenv("MISSION_MANAGER_ADDRESS")
        self.mission_manager_key = os.getenv("MISSION_MANAGER_PRIVATE_KEY")

        if not self.mission_manager_address or not self.mission_manager_key:
            raise ValueError("MISSION_MANAGER credentials not set")

        # Normalizar address
        self.mission_manager_address = self.w3.to_checksum_address(
            self.mission_manager_address
        )

        # Verificar balance
        balance = self.w3.eth.get_balance(self.mission_manager_address)
        balance_eth = self.w3.from_wei(balance, 'ether')
        logger.info(f"💰 Mission Manager balance: {balance_eth:.4f} ETH")

        if balance_eth < 0.01:
            logger.warning(f"⚠️ Low balance! Consider topping up.")

        # Cargar contrato
        self.contract_address = os.getenv("CONTRACT_ADDRESS")
        if not self.contract_address:
            raise ValueError("CONTRACT_ADDRESS not set")

        self.contract_address = self.w3.to_checksum_address(self.contract_address)

        # Cargar ABI
        abi_path = os.getenv("CONTRACT_ABI_PATH", "EmberholmPortal_ABI.json")
        if not os.path.exists(abi_path):
            raise FileNotFoundError(f"Contract ABI not found: {abi_path}")

        with open(abi_path, 'r') as f:
            contract_abi = json.load(f)

        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=contract_abi
        )

        logger.info(f"✅ Contract loaded: {self.contract_address}")


    def verify_signature(
        self,
        message: str,
        signature: str,
        expected_signer: str
    ) -> bool:
        """
        Verifica que una firma off-chain sea válida.

        Args:
            message: Mensaje firmado
            signature: Firma en hex
            expected_signer: Address esperada del firmante

        Returns:
            True si la firma es válida
        """
        try:
            # Codificar mensaje
            message_hash = encode_defunct(text=message)

            # Recuperar address del firmante
            recovered_address = self.w3.eth.account.recover_message(
                message_hash,
                signature=signature
            )

            # Normalizar addresses
            recovered_address = recovered_address.lower()
            expected_signer = expected_signer.lower()

            is_valid = recovered_address == expected_signer

            if is_valid:
                logger.info(f"✅ Signature verified for {expected_signer[:10]}...")
            else:
                logger.warning(
                    f"❌ Signature mismatch: expected {expected_signer[:10]}..., "
                    f"got {recovered_address[:10]}..."
                )

            return is_valid

        except Exception as e:
            logger.error(f"❌ Signature verification failed: {e}")
            return False


    def verify_nft_ownership(self, token_id: int, expected_owner: str) -> bool:
        """
        Verifica que un wallet sea owner de un NFT.

        Args:
            token_id: ID del NFT
            expected_owner: Address esperada

        Returns:
            True si es el owner
        """
        try:
            owner = self.contract.functions.ownerOf(token_id).call()
            owner = owner.lower()
            expected_owner = expected_owner.lower()

            is_owner = owner == expected_owner

            if not is_owner:
                logger.warning(
                    f"❌ Ownership mismatch for token #{token_id}: "
                    f"expected {expected_owner[:10]}..., got {owner[:10]}..."
                )

            return is_owner

        except ContractLogicError as e:
            logger.error(f"❌ Token #{token_id} doesn't exist: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to check ownership: {e}")
            return False


    def is_token_staked(self, token_id: int) -> bool:
        """
        Verifica si un NFT está stakeado.

        Args:
            token_id: ID del NFT

        Returns:
            True si está stakeado
        """
        try:
            is_staked = self.contract.functions.stakedTokens(token_id).call()
            return is_staked
        except Exception as e:
            logger.error(f"❌ Failed to check stake status: {e}")
            return False


    def stake_token(self, token_id: int, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
        """
        Stakea un NFT on-chain (backend paga el gas).

        Args:
            token_id: ID del NFT a stakear
            max_retries: Número máximo de reintentos

        Returns:
            (success: bool, tx_hash: str)
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Staking token #{token_id} (attempt {attempt}/{max_retries})...")

                # Verificar que no esté ya stakeado
                if self.is_token_staked(token_id):
                    logger.warning(f"⚠️ Token #{token_id} already staked")
                    return (True, None)  # Ya stakeado = éxito

                # Get nonce
                nonce = self.w3.eth.get_transaction_count(self.mission_manager_address)

                # Build transaction
                tx = self.contract.functions.stakeToken(token_id).build_transaction({
                    'from': self.mission_manager_address,
                    'nonce': nonce,
                    'gas': 150000,  # Gas limit
                    'maxFeePerGas': self.w3.eth.gas_price * 2,  # 2x para prioridad
                    'maxPriorityFeePerGas': self.w3.to_wei(1, 'gwei')
                })

                # Sign transaction
                signed_tx = self.w3.eth.account.sign_transaction(
                    tx,
                    self.mission_manager_key
                )

                # Send transaction
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()

                logger.info(f"📤 Transaction sent: {tx_hash_hex}")

                # Wait for confirmation (timeout 2 minutos)
                receipt = self.w3.eth.wait_for_transaction_receipt(
                    tx_hash,
                    timeout=120
                )

                # Check status
                if receipt.status == 1:
                    gas_used = receipt.gasUsed
                    gas_price = receipt.effectiveGasPrice
                    cost_wei = gas_used * gas_price
                    cost_eth = self.w3.from_wei(cost_wei, 'ether')

                    logger.info(f"✅ Token #{token_id} staked successfully!")
                    logger.info(f"💰 Gas used: {gas_used} (~{cost_eth:.6f} ETH)")
                    logger.info(f"🔗 TX: {tx_hash_hex}")

                    return (True, tx_hash_hex)
                else:
                    logger.error(f"❌ Transaction failed (status=0)")

                    if attempt < max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.info(f"⏳ Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue

                    return (False, None)

            except TimeExhausted:
                logger.error(f"⏰ Transaction timeout for token #{token_id}")
                if attempt < max_retries:
                    logger.info(f"⏳ Retrying...")
                    continue
                return (False, None)

            except Exception as e:
                logger.error(f"❌ Stake failed: {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return (False, None)

        return (False, None)


    def unstake_token(self, token_id: int, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
        """
        Unstakea un NFT on-chain (backend paga el gas).

        Args:
            token_id: ID del NFT a unstakear
            max_retries: Número máximo de reintentos

        Returns:
            (success: bool, tx_hash: str)
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Unstaking token #{token_id} (attempt {attempt}/{max_retries})...")

                # Verificar que esté stakeado
                if not self.is_token_staked(token_id):
                    logger.warning(f"⚠️ Token #{token_id} not staked")
                    return (True, None)  # Ya unstakeado = éxito

                # Get nonce
                nonce = self.w3.eth.get_transaction_count(self.mission_manager_address)

                # Build transaction
                tx = self.contract.functions.unstakeToken(token_id).build_transaction({
                    'from': self.mission_manager_address,
                    'nonce': nonce,
                    'gas': 100000,
                    'maxFeePerGas': self.w3.eth.gas_price * 2,
                    'maxPriorityFeePerGas': self.w3.to_wei(1, 'gwei')
                })

                # Sign transaction
                signed_tx = self.w3.eth.account.sign_transaction(
                    tx,
                    self.mission_manager_key
                )

                # Send transaction
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()

                logger.info(f"📤 Transaction sent: {tx_hash_hex}")

                # Wait for confirmation
                receipt = self.w3.eth.wait_for_transaction_receipt(
                    tx_hash,
                    timeout=120
                )

                # Check status
                if receipt.status == 1:
                    gas_used = receipt.gasUsed
                    gas_price = receipt.effectiveGasPrice
                    cost_wei = gas_used * gas_price
                    cost_eth = self.w3.from_wei(cost_wei, 'ether')

                    logger.info(f"✅ Token #{token_id} unstaked successfully!")
                    logger.info(f"💰 Gas used: {gas_used} (~{cost_eth:.6f} ETH)")
                    logger.info(f"🔗 TX: {tx_hash_hex}")

                    return (True, tx_hash_hex)
                else:
                    logger.error(f"❌ Transaction failed (status=0)")

                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        logger.info(f"⏳ Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue

                    return (False, None)

            except TimeExhausted:
                logger.error(f"⏰ Transaction timeout for token #{token_id}")
                if attempt < max_retries:
                    logger.info(f"⏳ Retrying...")
                    continue
                return (False, None)

            except Exception as e:
                logger.error(f"❌ Unstake failed: {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return (False, None)

        return (False, None)


    def get_token_info(self, token_id: int) -> Optional[dict]:
        """
        Obtiene información on-chain de un token.

        Args:
            token_id: ID del NFT

        Returns:
            Dict con info del token o None si falla
        """
        try:
            info = self.contract.functions.getTokenInfo(token_id).call()

            return {
                'tokenId': info[0],
                'owner': info[1],
                'isStaked': info[2],
                'stakedSince': info[3]
            }

        except Exception as e:
            logger.error(f"❌ Failed to get token info: {e}")
            return None


# Singleton instance
_web3_manager = None

def get_web3_manager() -> Web3Manager:
    """
    Obtiene la instancia singleton del Web3Manager.

    Returns:
        Web3Manager instance
    """
    global _web3_manager
    if _web3_manager is None:
        _web3_manager = Web3Manager()
    return _web3_manager
