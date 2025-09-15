import { createSlice } from '@reduxjs/toolkit'

const initialState = {
}

const telemetrySlice = createSlice({
  name: 'telemetry',
  initialState,
  reducers: {
  }
})

export const {
} = telemetrySlice.actions

export default telemetrySlice.reducer