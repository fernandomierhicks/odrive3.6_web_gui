// This should be inside device List Component
// {isConnected && connectedDevice && (
//   <Box mt={4} p={3} bg="gray.700" borderRadius="md">
//     <VStack spacing={2} align="stretch">
//       <HStack justify="space-between">
//         <Box fontSize="sm" color="gray.300">Status:</Box>
//         <Badge colorScheme="green" variant="solid">Connected</Badge>
//       </HStack>
//       <HStack justify="space-between">
//         <Box fontSize="sm" color="gray.300">Device:</Box>
//         <Box fontSize="sm" color="white">{connectedDevice.path}</Box>
//       </HStack>
//       <HStack justify="space-between">
//         <Box fontSize="sm" color="gray.300">Serial:</Box>
//         <Box fontSize="sm" color="white" fontFamily="mono">
//           {connectedDevice.serial}
//         </Box>
//       </HStack>
//       <HStack justify="space-between">
//         <Box fontSize="sm" color="gray.300">Firmware:</Box>
//         <Box fontSize="sm" color="odrive.300">{connectedDevice.fw_version}</Box>
//       </HStack>
//     </VStack>
//   </Box>
// )}