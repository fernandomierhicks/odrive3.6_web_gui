import { Box, Heading, Text } from '@chakra-ui/react'

const InspectorTab = () => {
  return (
    <Box p={6}>
      <Heading size="md" color="odrive.300">Inspector</Heading>
      <Text mt={2} color="gray.300">Inspect properties and state.</Text>
    </Box>
  )
}

export default InspectorTab