const hre = require("hardhat");

async function main() {
  console.log("\n🚀 Deploying EmberholmPortal to Base Mainnet...\n");

  // Treasury address (receives mint funds and royalties)
  const TREASURY_ADDRESS = "0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B";

  console.log("📋 Deployment Configuration:");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("Network:", hre.network.name);
  console.log("Chain ID:", hre.network.config.chainId);
  console.log("Treasury:", TREASURY_ADDRESS);
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  // Get deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("🔑 Deployer address:", deployer.address);

  // Check deployer balance
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("💰 Deployer balance:", hre.ethers.formatEther(balance), "ETH");

  if (balance < hre.ethers.parseEther("0.005")) {
    console.log("⚠️  WARNING: Low balance! You might need more ETH for deployment.");
  }

  console.log("\n⏳ Deploying contract...\n");

  // Deploy contract
  const EmberholmPortal = await hre.ethers.getContractFactory("EmberholmPortal");
  const portal = await EmberholmPortal.deploy(TREASURY_ADDRESS);

  await portal.waitForDeployment();
  const contractAddress = await portal.getAddress();

  console.log("✅ EmberholmPortal deployed successfully!");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("📍 Contract Address:", contractAddress);
  console.log("🔍 Basescan:", `https://basescan.org/address/${contractAddress}`);
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  // Wait for block confirmations
  console.log("⏳ Waiting for block confirmations...");
  await portal.deploymentTransaction().wait(5);
  console.log("✅ 5 confirmations received\n");

  // Verify contract on Basescan
  console.log("📝 Verifying contract on Basescan...");
  try {
    await hre.run("verify:verify", {
      address: contractAddress,
      constructorArguments: [TREASURY_ADDRESS],
    });
    console.log("✅ Contract verified on Basescan!\n");
  } catch (error) {
    if (error.message.includes("Already Verified")) {
      console.log("✅ Contract already verified!\n");
    } else {
      console.log("⚠️  Verification failed. You can verify manually:");
      console.log(`npx hardhat verify --network base ${contractAddress} ${TREASURY_ADDRESS}\n`);
      console.log("Error:", error.message, "\n");
    }
  }

  // Display contract info
  console.log("📊 Contract Information:");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

  const mintPrice = await portal.mintPrice();
  const maxSupply = await portal.maxSupply();
  const treasury = await portal.treasury();

  console.log("Name: Emberholm Portal");
  console.log("Symbol: EMBERHOLM");
  console.log("Max Supply:", maxSupply.toString());
  console.log("Mint Price:", hre.ethers.formatEther(mintPrice), "ETH");
  console.log("Treasury:", treasury);
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  console.log("🎉 Deployment Complete!\n");
  console.log("📝 Next Steps:");
  console.log("1. ✅ Contract deployed and verified");
  console.log("2. 🔧 Set Mission Manager wallet (optional):");
  console.log(`   npx hardhat run scripts/setMissionManager.js --network base`);
  console.log("3. 🌐 Update frontend with contract address:", contractAddress);
  console.log("4. 🔙 Update backend with contract address:", contractAddress);
  console.log("5. 🧪 Test mint function on Basescan");
  console.log("6. 🎨 Verify metadata endpoint works\n");

  // Save deployment info
  const fs = require("fs");
  const deploymentInfo = {
    network: hre.network.name,
    chainId: hre.network.config.chainId,
    contractAddress: contractAddress,
    treasury: TREASURY_ADDRESS,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    basescanUrl: `https://basescan.org/address/${contractAddress}`,
    transactionHash: portal.deploymentTransaction().hash
  };

  fs.writeFileSync(
    "deployment-info.json",
    JSON.stringify(deploymentInfo, null, 2)
  );
  console.log("💾 Deployment info saved to: deployment-info.json\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed!\n");
    console.error(error);
    process.exit(1);
  });
