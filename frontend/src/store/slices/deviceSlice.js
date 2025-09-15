import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  availableDevices: [],
  connectedDevice: null,
}

const deviceSlice = createSlice({
  name: 'device',
  initialState,
  reducers: {
  }
})

export const {
} = deviceSlice.actions

export default deviceSlice.reducer